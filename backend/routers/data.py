import os
import shutil
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Business, DataImportJob, Invoice, Transaction

try:
    from celery.result import AsyncResult
    from backend.tasks.celery_app import celery_app
    from backend.tasks.processing_tasks import (
        process_tally_upload,
        process_gst_upload,
        process_bank_upload,
    )
except ModuleNotFoundError:
    AsyncResult = None
    celery_app = None
    process_tally_upload = None
    process_gst_upload = None
    process_bank_upload = None

router = APIRouter(prefix="/data", tags=["Data"])

# Ensure temp directory exists
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)


@router.post("/upload")
async def upload_data(
    business_id: int = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint to upload Tally XML, GST JSON, or Bank statement CSV files.
    Saves file to temp storage and queues corresponding Celery background parsing task.
    """
    file_type_cleaned = file_type.strip().lower()
    if file_type_cleaned not in ["tally", "gst", "bank"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file_type. Must be 'tally', 'gst', or 'bank'.",
        )
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file is required.",
        )
    allowed_extensions = {
        "tally": (".xml",),
        "gst": (".json",),
        "bank": (".csv",),
    }
    if not file.filename.lower().endswith(allowed_extensions[file_type_cleaned]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension for {file_type_cleaned}.",
        )
    if celery_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload processing is unavailable because Celery is not installed in this environment.",
        )

    # ── Read file into memory instead of saving to disk ──
    # Since FastAPI and Celery run in separate containers on Railway without shared storage,
    # we pass the text content directly in the task payload.
    try:
        content_bytes = await file.read()
        text_content = content_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {e}",
        )

    task_id = str(uuid4())
    job = DataImportJob(
        business_id=business_id,
        task_id=task_id,
        file_type=file_type_cleaned,
        filename=file.filename,
        status="queued",
        percent=0,
        message="Queued in background",
    )
    db.add(job)
    await db.commit()

    # Queue Celery task with the raw string content instead of file path
    if file_type_cleaned == "tally":
        process_tally_upload.apply_async(args=[text_content, business_id], task_id=task_id)
    elif file_type_cleaned == "gst":
        # Pass filename to infer GSTR type inside the task
        process_gst_upload.apply_async(args=[text_content, business_id, file.filename], task_id=task_id)
    elif file_type_cleaned == "bank":
        process_bank_upload.apply_async(args=[text_content, business_id], task_id=task_id)

    return {
        "message": "File uploaded successfully, processing started",
        "task_id": task_id,
        "file_type": file_type_cleaned,
    }


@router.get("/status/{task_id}")
async def get_upload_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the execution state and progress metadata of a Celery upload processing task.
    """
    if AsyncResult is None or celery_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload status is unavailable because Celery is not installed in this environment.",
        )

    job_result = await db.execute(
        select(DataImportJob).where(DataImportJob.task_id == task_id)
    )
    job = job_result.scalars().first()

    res = AsyncResult(task_id, app=celery_app)

    try:
        state = res.state
        info = res.info
        result_value = res.result
    except Exception as exc:
        if job:
            return {
                "task_id": task_id,
                "state": job.status.upper(),
                "percent": job.percent,
                "status": job.message,
                "error": job.error_message,
                "result": job.result or None,
            }
        return {
            "task_id": task_id,
            "state": "FAILURE",
            "percent": 100,
            "status": "Failed",
            "error": f"Could not decode task result. Re-upload the file after restarting the Celery worker. Detail: {exc}",
            "result": None,
        }

    percent = 0
    status_msg = "Pending"
    error_msg = None
    result = None

    if state == "PENDING":
        percent = 0
        status_msg = "Queued in background"
    elif state == "PROGRESS":
        info = info or {}
        percent = info.get("percent", 50)
        status_msg = info.get("status", "Processing")
    elif state == "SUCCESS":
        percent = 100
        status_msg = "Processing completed successfully"
        result = result_value
    elif state == "FAILURE":
        percent = 100
        status_msg = "Failed"
        # Extract error message if available
        if isinstance(info, dict):
            error_msg = info.get("error", str(info))
        else:
            error_msg = str(info)
    else:
        status_msg = state

    if job:
        job.status = state.lower()
        job.percent = percent
        job.message = status_msg
        job.error_message = error_msg
        if state in {"SUCCESS", "FAILURE"} and job.completed_at is None:
            job.completed_at = datetime.utcnow()
        if isinstance(result, dict):
            job.result = result
            job.records_added = int(
                result.get("added_records")
                or result.get("added_transactions")
                or result.get("added_invoices")
                or 0
            )
        db.add(job)
        await db.commit()

    return {
        "task_id": task_id,
        "state": state,
        "percent": percent,
        "status": status_msg,
        "error": error_msg,
        "result": result,
    }


@router.get("/integrations/{business_id}")
async def get_integrations_summary(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    business_result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = business_result.scalars().first()

    source_counts_result = await db.execute(
        select(Transaction.source, func.count(Transaction.id))
        .where(Transaction.business_id == business_id)
        .group_by(Transaction.source)
    )
    source_counts = {
        source: int(count) for source, count in source_counts_result.all()
    }

    gst_invoice_count_result = await db.execute(
        select(func.count()).select_from(Invoice).where(
            Invoice.business_id == business_id,
            Invoice.source == "gst",
        )
    )
    gst_invoice_count = int(gst_invoice_count_result.scalar() or 0)

    connected_sources = business.data_sources_connected if business else []
    if gst_invoice_count == 0 and "gst" in connected_sources:
        # Dev fallback for invoices inserted before the invoice.source column existed.
        legacy_gst_invoice_count_result = await db.execute(
            select(func.count()).select_from(Invoice).where(Invoice.business_id == business_id)
        )
        gst_invoice_count = int(legacy_gst_invoice_count_result.scalar() or 0)

    source_counts["gst"] = max(source_counts.get("gst", 0), gst_invoice_count)

    latest_by_source = {}
    for source in ["tally", "bank"]:
        latest_result = await db.execute(
            select(Transaction)
            .where(
                Transaction.business_id == business_id,
                Transaction.source == source,
            )
            .order_by(desc(Transaction.date), desc(Transaction.id))
            .limit(1)
        )
        latest = latest_result.scalars().first()
        latest_by_source[source] = latest.date.isoformat() if latest else None

    latest_gst_invoice_result = await db.execute(
        select(Invoice)
        .where(Invoice.business_id == business_id)
        .order_by(desc(Invoice.issue_date), desc(Invoice.id))
        .limit(1)
    )
    latest_gst_invoice = latest_gst_invoice_result.scalars().first()
    latest_by_source["gst"] = latest_gst_invoice.issue_date.isoformat() if latest_gst_invoice else None

    jobs_result = await db.execute(
        select(DataImportJob)
        .where(DataImportJob.business_id == business_id)
        .order_by(desc(DataImportJob.created_at), desc(DataImportJob.id))
        .limit(5)
    )
    recent_jobs = jobs_result.scalars().all()

    return {
        "business_id": business_id,
        "quality_score": business.quality_score if business else 0,
        "connected_sources": [
            {
                "type": source,
                "label": {
                    "tally": "Tally / ERP",
                    "gst": "GST Portal",
                    "bank": "Bank Statements",
                }.get(source, source.title()),
                "status": "connected" if source in connected_sources or source_counts.get(source, 0) > 0 else "not_connected",
                "records": source_counts.get(source, 0),
                "last_sync": latest_by_source.get(source),
            }
            for source in ["tally", "gst", "bank"]
        ],
        "recent_activity": [
            {
                "task_id": job.task_id,
                "file_type": job.file_type,
                "filename": job.filename,
                "status": job.status,
                "percent": job.percent,
                "message": job.message,
                "records_added": job.records_added,
                "error": job.error_message,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in recent_jobs
        ],
        "supported_uploads": [
            {"type": "tally", "label": "Tally XML", "accept": ".xml"},
            {"type": "gst", "label": "GST JSON", "accept": ".json"},
            {"type": "bank", "label": "Bank CSV", "accept": ".csv"},
        ],
    }
