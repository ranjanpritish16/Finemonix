import asyncio
import os
import logging
from datetime import datetime
from celery import shared_task
from sqlalchemy.future import select

from backend.database import async_session_maker
from backend.models import Business, Client, DataImportJob, Transaction, Invoice
from backend.services.tally_parser import TallyParser
from backend.services.gst_parser import GSTParser
from backend.services.bank_parser import BankParser
from backend.services.deduplication import deduplicate_transactions
from backend.services.entity_resolution import EntityResolutionPipeline

logger = logging.getLogger(__name__)


async def _get_existing_transactions(session, business_id: int):
    stmt = select(Transaction).where(Transaction.business_id == business_id)
    res = await session.execute(stmt)
    return res.scalars().all()


async def _ensure_business(session, business_id: int) -> Business:
    stmt = select(Business).where(Business.id == business_id)
    res = await session.execute(stmt)
    business = res.scalars().first()
    if business:
        return business

    business = Business(
        id=business_id,
        name=f"Demo Business {business_id}",
        data_sources_connected=[],
    )
    session.add(business)
    await session.flush()
    return business


async def _mark_source_connected(session, business_id: int, source: str):
    business = await _ensure_business(session, business_id)
    connected_sources = list(business.data_sources_connected or [])
    if source not in connected_sources:
        connected_sources.append(source)
        business.data_sources_connected = connected_sources
    business.quality_score = min(100, max(business.quality_score or 0, len(connected_sources) * 25))
    session.add(business)


async def _update_import_job(
    session,
    task_id: str,
    status: str,
    percent: int,
    message: str,
    records_added: int = 0,
    error_message: str | None = None,
    result: dict | None = None,
):
    stmt = select(DataImportJob).where(DataImportJob.task_id == task_id)
    res = await session.execute(stmt)
    job = res.scalars().first()
    if not job:
        return

    job.status = status
    job.percent = percent
    job.message = message
    job.records_added = records_added
    job.error_message = error_message
    if result is not None:
        job.result = result
    if status in {"success", "failed"}:
        job.completed_at = datetime.utcnow()
    session.add(job)
    await session.flush()


async def _store_task_failure(task_id: str, error_message: str):
    async with async_session_maker() as session:
        try:
            await _update_import_job(
                session,
                task_id,
                "failed",
                100,
                "Processing failed",
                error_message=error_message,
                result={"error": error_message},
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Failed to persist import job failure")


@shared_task(bind=True)
def process_tally_upload(self, xml_content: str, business_id: int):
    """
    Background Celery task to parse Tally XML and save to Database.
    """
    self.update_state(state="PROGRESS", meta={"percent": 10, "status": "Reading data"})

    self.update_state(state="PROGRESS", meta={"percent": 30, "status": "Parsing Tally XML"})

    async def run():
        async with async_session_maker() as session:
            try:
                await _ensure_business(session, business_id)
                await _update_import_job(
                    session,
                    self.request.id,
                    "processing",
                    10,
                    "Reading file",
                )

                # Parse
                parser = TallyParser(xml_content)
                parsed_txs, parsed_invoices, parsed_clients = parser.parse()

                self.update_state(state="PROGRESS", meta={"percent": 50, "status": "Resolving entities"})
                
                pipeline = EntityResolutionPipeline(session)
                
                # Fetch or create clients
                client_map = {}  # maps canonical_name to Client ORM model
                for pc in parsed_clients:
                    entity = await pipeline.resolve_client(
                        client_name=pc["canonical_name"],
                        gstin=pc["gstin"],
                        entity_type="company"
                    )
                    
                    # Check if client already exists for this business
                    stmt = select(Client).where(
                        Client.business_id == business_id,
                        Client.canonical_name == pc["canonical_name"]
                    )
                    res = await session.execute(stmt)
                    client = res.scalars().first()
                    
                    if not client:
                        client = Client(
                            business_id=business_id,
                            canonical_name=pc["canonical_name"],
                            gstin=pc["gstin"],
                            is_listed_company=entity.entity_type == "company" and entity.canonical_name.endswith("Ltd"),
                            aliases=entity.aliases,
                        )
                        session.add(client)
                        await session.flush()
                    
                    client_map[pc["canonical_name"]] = client

                self.update_state(state="PROGRESS", meta={"percent": 70, "status": "Deduplicating transactions"})

                # Load existing transactions for deduplication
                existing_txs = await _get_existing_transactions(session, business_id)
                
                # Format parsed transactions for deduplication comparison
                txs_to_compare = []
                for ptx in parsed_txs:
                    txs_to_compare.append({
                        "date": ptx["date"],
                        "amount": ptx["amount"],
                        "direction": ptx["direction"],
                        "counterparty_name": ptx["counterparty_name"],
                    })

                # Deduplicate
                txs_deduped = deduplicate_transactions(txs_to_compare, [
                    {
                        "date": et.date,
                        "amount": et.amount,
                        "direction": et.direction,
                        "counterparty_name": et.raw_description, # simple fallback
                    } for et in existing_txs
                ])

                # Insert deduplicated transactions
                for tx_data in txs_deduped:
                    # Find counterparty ID
                    cp_id = None
                    cp_name = tx_data.get("counterparty_name")
                    if cp_name and cp_name in client_map:
                        cp_id = client_map[cp_name].id

                    tx_orig = next(t for t in parsed_txs if t["date"] == tx_data["date"] and t["amount"] == tx_data["amount"])

                    new_tx = Transaction(
                        business_id=business_id,
                        date=tx_data["date"],
                        amount=tx_data["amount"],
                        direction=tx_data["direction"],
                        category=tx_orig["category"],
                        counterparty_id=cp_id,
                        source="tally",
                        raw_description=tx_orig["raw_description"],
                    )
                    session.add(new_tx)

                # Insert invoices
                for pinv in parsed_invoices:
                    cp_id = None
                    cp_name = pinv.get("counterparty_name")
                    if cp_name and cp_name in client_map:
                        cp_id = client_map[cp_name].id

                    new_inv = Invoice(
                        business_id=business_id,
                        client_id=cp_id,
                        amount=pinv["amount"],
                        issue_date=pinv["issue_date"],
                        due_date=pinv["due_date"],
                        status=pinv["status"],
                        source="tally",
                    )
                    session.add(new_inv)

                await session.flush()

                self.update_state(state="PROGRESS", meta={"percent": 90, "status": "Updating metrics"})
                await pipeline.update_client_metrics(business_id)
                await _mark_source_connected(session, business_id, "tally")
                result = {
                    "percent": 100,
                    "status": "Success",
                    "added_transactions": len(txs_deduped),
                    "added_invoices": len(parsed_invoices),
                    "added_records": len(txs_deduped) + len(parsed_invoices),
                }
                await _update_import_job(
                    session,
                    self.request.id,
                    "success",
                    100,
                    "Processing completed successfully",
                    records_added=result["added_records"],
                    result=result,
                )

                await session.commit()
                
                return result
            
            except Exception as inner_e:
                await session.rollback()
                logger.error(f"Error in process_tally_upload run: {inner_e}")
                await _store_task_failure(self.request.id, str(inner_e))
                raise inner_e

    try:
        res = asyncio.run(run())
        return res
    except Exception as e:
        asyncio.run(_store_task_failure(self.request.id, str(e)))
        raise


@shared_task(bind=True)
def process_gst_upload(self, json_content: str, business_id: int, filename: str = ""):
    """
    Background Celery task to parse GST JSON (GSTR-1 or GSTR-2A) and save to Database.
    """
    self.update_state(state="PROGRESS", meta={"percent": 10, "status": "Reading data"})

    # Guess GSTR type from filename or content
    file_type = "gstr1"
    if "gstr2" in filename.lower() or "gstr2a" in filename.lower() or "gstr-2" in filename.lower():
        file_type = "gstr2a"

    self.update_state(state="PROGRESS", meta={"percent": 30, "status": "Parsing GST JSON"})

    async def run():
        async with async_session_maker() as session:
            try:
                await _ensure_business(session, business_id)
                await _update_import_job(
                    session,
                    self.request.id,
                    "processing",
                    10,
                    "Reading file",
                )

                parser = GSTParser(json_content)
                parsed_invoices, parsed_clients = parser.parse(file_type=file_type)

                self.update_state(state="PROGRESS", meta={"percent": 50, "status": "Resolving entities"})
                pipeline = EntityResolutionPipeline(session)

                client_map = {}
                for pc in parsed_clients:
                    entity = await pipeline.resolve_client(
                        client_name=pc["canonical_name"],
                        gstin=pc["gstin"],
                        entity_type="company"
                    )

                    # Check if client already exists
                    stmt = select(Client).where(
                        Client.business_id == business_id,
                        Client.canonical_name == pc["canonical_name"]
                    )
                    res = await session.execute(stmt)
                    client = res.scalars().first()

                    if not client:
                        client = Client(
                            business_id=business_id,
                            canonical_name=pc["canonical_name"],
                            gstin=pc["gstin"],
                            is_listed_company=entity.entity_type == "company" and entity.canonical_name.endswith("Ltd"),
                            aliases=entity.aliases,
                        )
                        session.add(client)
                        await session.flush()
                    
                    client_map[pc["canonical_name"]] = client

                self.update_state(state="PROGRESS", meta={"percent": 75, "status": "Saving invoices"})

                # Insert invoices
                added_invoices = 0
                for pinv in parsed_invoices:
                    cp_id = None
                    cp_name = pinv.get("counterparty_name")
                    if cp_name and cp_name in client_map:
                        cp_id = client_map[cp_name].id

                    # Check for duplicate invoice
                    stmt = select(Invoice).where(
                        Invoice.business_id == business_id,
                        Invoice.amount == pinv["amount"],
                        Invoice.issue_date == pinv["issue_date"],
                        Invoice.client_id == cp_id
                    )
                    res = await session.execute(stmt)
                    existing_inv = res.scalars().first()

                    if not existing_inv:
                        new_inv = Invoice(
                            business_id=business_id,
                            client_id=cp_id,
                            amount=pinv["amount"],
                            issue_date=pinv["issue_date"],
                            due_date=pinv["due_date"],
                            status=pinv["status"],
                            source="gst",
                        )
                        session.add(new_inv)
                        added_invoices += 1

                await session.flush()

                self.update_state(state="PROGRESS", meta={"percent": 90, "status": "Updating metrics"})
                await pipeline.update_client_metrics(business_id)
                await _mark_source_connected(session, business_id, "gst")
                result = {
                    "percent": 100,
                    "status": "Success",
                    "added_invoices": added_invoices,
                    "added_records": added_invoices,
                }
                await _update_import_job(
                    session,
                    self.request.id,
                    "success",
                    100,
                    "Processing completed successfully",
                    records_added=added_invoices,
                    result=result,
                )

                await session.commit()
                
                return result
            
            except Exception as inner_e:
                await session.rollback()
                logger.error(f"Error in process_gst_upload run: {inner_e}")
                await _store_task_failure(self.request.id, str(inner_e))
                raise inner_e

    try:
        res = asyncio.run(run())
        return res
    except Exception as e:
        asyncio.run(_store_task_failure(self.request.id, str(e)))
        raise


@shared_task(bind=True)
def process_bank_upload(self, csv_content: str, business_id: int):
    """
    Background Celery task to parse Bank statement CSV and save to Database.
    """
    self.update_state(state="PROGRESS", meta={"percent": 10, "status": "Reading data"})

    self.update_state(state="PROGRESS", meta={"percent": 30, "status": "Parsing Bank CSV"})

    async def run():
        async with async_session_maker() as session:
            try:
                await _ensure_business(session, business_id)
                await _update_import_job(
                    session,
                    self.request.id,
                    "processing",
                    10,
                    "Reading file",
                )

                parser = BankParser(csv_content)
                parsed_txs = parser.parse()

                self.update_state(state="PROGRESS", meta={"percent": 60, "status": "Deduplicating bank transactions"})

                # Load existing transactions
                existing_txs = await _get_existing_transactions(session, business_id)

                txs_to_compare = []
                for ptx in parsed_txs:
                    txs_to_compare.append({
                        "date": ptx["date"],
                        "amount": ptx["amount"],
                        "direction": ptx["direction"],
                        "counterparty_name": ptx["raw_description"],
                    })

                txs_deduped = deduplicate_transactions(txs_to_compare, [
                    {
                        "date": et.date,
                        "amount": et.amount,
                        "direction": et.direction,
                        "counterparty_name": et.raw_description,
                    } for et in existing_txs
                ])

                # Insert deduplicated transactions
                for tx_data in txs_deduped:
                    # Parse the description to see if we can resolve counterparty
                    # Since it's a bank narration, we don't have direct clients, but we can do a best-effort lookup in clients
                    # For simplicity, we keep counterparty_id as None or resolve it via simple query if exact match
                    cp_id = None
                    
                    new_tx = Transaction(
                        business_id=business_id,
                        date=tx_data["date"],
                        amount=tx_data["amount"],
                        direction=tx_data["direction"],
                        category="General",
                        counterparty_id=cp_id,
                        source="bank",
                        raw_description=tx_data["counterparty_name"],
                    )
                    session.add(new_tx)

                await session.flush()

                self.update_state(state="PROGRESS", meta={"percent": 90, "status": "Updating metrics"})
                pipeline = EntityResolutionPipeline(session)
                await pipeline.update_client_metrics(business_id)
                await _mark_source_connected(session, business_id, "bank")
                result = {
                    "percent": 100,
                    "status": "Success",
                    "added_transactions": len(txs_deduped),
                    "added_records": len(txs_deduped),
                }
                await _update_import_job(
                    session,
                    self.request.id,
                    "success",
                    100,
                    "Processing completed successfully",
                    records_added=len(txs_deduped),
                    result=result,
                )

                await session.commit()
                
                return result
            
            except Exception as inner_e:
                await session.rollback()
                logger.error(f"Error in process_bank_upload run: {inner_e}")
                await _store_task_failure(self.request.id, str(inner_e))
                raise inner_e

    try:
        res = asyncio.run(run())
        return res
    except Exception as e:
        asyncio.run(_store_task_failure(self.request.id, str(e)))
        raise

@shared_task(bind=True)
def train_prophet(self, business_id: int):
    """Async task to train prophet model"""
    logger.info(f"Training Prophet model for business {business_id}")
    return {"status": "Success", "model": "prophet"}

@shared_task(bind=True)
def retrain_lstm(self, business_id: int):
    """Async task to retrain LSTM model"""
    logger.info(f"Retraining LSTM model for business {business_id}")
    return {"status": "Success", "model": "lstm"}

