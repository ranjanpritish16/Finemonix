import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Business, Transaction

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
    if celery_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload processing is unavailable because Celery is not installed in this environment.",
        )

    # Save uploaded file to temp path
    filename = f"biz_{business_id}_{file_type_cleaned}_{file.filename}"
    temp_file_path = os.path.join(TEMP_DIR, filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e}",
        )

    # Queue Celery task
    task_id = None
    if file_type_cleaned == "tally":
        task = process_tally_upload.delay(temp_file_path, business_id)
        task_id = task.id
    elif file_type_cleaned == "gst":
        task = process_gst_upload.delay(temp_file_path, business_id)
        task_id = task.id
    elif file_type_cleaned == "bank":
        task = process_bank_upload.delay(temp_file_path, business_id)
        task_id = task.id

    return {
        "message": "File uploaded successfully, processing started",
        "task_id": task_id,
        "file_type": file_type_cleaned,
    }


@router.get("/status/{task_id}")
async def get_upload_status(task_id: str):
    """
    Returns the execution state and progress metadata of a Celery upload processing task.
    """
    if AsyncResult is None or celery_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload status is unavailable because Celery is not installed in this environment.",
        )

    res = AsyncResult(task_id, app=celery_app)

    try:
        state = res.state
        info = res.info
        result_value = res.result
    except Exception as exc:
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

    latest_by_source = {}
    for source in ["tally", "gst", "bank"]:
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

    connected_sources = business.data_sources_connected if business else []

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
        "supported_uploads": [
            {"type": "tally", "label": "Tally XML", "accept": ".xml"},
            {"type": "gst", "label": "GST JSON", "accept": ".json"},
            {"type": "bank", "label": "Bank CSV", "accept": ".csv"},
        ],
    }
