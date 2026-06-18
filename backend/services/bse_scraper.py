# backend/services/bse_scraper.py

import asyncio
import hashlib
import random
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
from lxml import etree
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import Filing

logger = logging.getLogger(__name__)

BSE_XML_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/{scrip_code}.xml"
PDF_BASE_DIR = Path("data/filings")

DEMO_COMPANIES = {
    "DHFL":     "532720",
    "YESBANK":  "532648",
    "INFY":     "500209",
}


def _make_dedup_hash(filing_date: str, subject: str, bse_code: str) -> str:
    raw = f"{filing_date}|{subject.strip().lower()[:100]}|{bse_code.upper()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _parse_bse_date(date_str: str) -> Optional[date]:
    for fmt in ("%Y%m%d", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _classify_filing(subject: str) -> str:
    s = subject.lower()
    if any(k in s for k in ["board meeting", "board of director"]):
        return "BoardMeeting"
    elif any(k in s for k in ["annual report", "annual general"]):
        return "AnnualReport"
    elif any(k in s for k in ["quarterly result", "financial result", "q1", "q2", "q3", "q4"]):
        return "FinancialResults"
    elif any(k in s for k in ["pledge", "encumber"]):
        return "SharePledge"
    elif any(k in s for k in ["auditor", "audit"]):
        return "AuditReport"
    return "General"


def _get_mock_announcements(
    scrip_code: str,
    lookback_days: int,
) -> List[Dict[str, Any]]:
    """Realistic mock filings for demo companies — always returns full history."""
    mock_db = {
        "532720": [  # DHFL
            {"news_id": "DHFL-2018Q3-001", "subject": "Quarterly Financial Results Q3 2018", "filing_date": date(2018, 10, 15), "filing_type": "FinancialResults"},
            {"news_id": "DHFL-2018Q3-002", "subject": "Board Meeting - Promoter Share Pledge Update", "filing_date": date(2018, 9, 21), "filing_type": "SharePledge"},
            {"news_id": "DHFL-2018Q2-001", "subject": "Quarterly Financial Results Q2 2018", "filing_date": date(2018, 7, 14), "filing_type": "FinancialResults"},
            {"news_id": "DHFL-2018-AR",    "subject": "Annual Report 2017-18 with Auditor Observations", "filing_date": date(2018, 8, 30), "filing_type": "AnnualReport"},
            {"news_id": "DHFL-2019Q1-001", "subject": "Quarterly Financial Results Q1 2019 - Delayed Filing", "filing_date": date(2019, 1, 22), "filing_type": "FinancialResults"},
            {"news_id": "DHFL-2019-001",   "subject": "RBI Inquiry - Response to Regulatory Notice", "filing_date": date(2019, 3, 5), "filing_type": "General"},
            {"news_id": "DHFL-2017Q4-001", "subject": "Quarterly Financial Results Q4 2017", "filing_date": date(2017, 4, 18), "filing_type": "FinancialResults"},
            {"news_id": "DHFL-2017-AR",    "subject": "Annual Report 2016-17", "filing_date": date(2017, 8, 25), "filing_type": "AnnualReport"},
        ],
        "532648": [  # YESBANK
            {"news_id": "YES-2019Q1-001",  "subject": "Quarterly Financial Results Q1 2019", "filing_date": date(2019, 4, 27), "filing_type": "FinancialResults"},
            {"news_id": "YES-2019-001",    "subject": "RBI Directive on CEO Tenure - Board Response", "filing_date": date(2019, 1, 31), "filing_type": "General"},
            {"news_id": "YES-2018Q4-001",  "subject": "Quarterly Financial Results Q4 2018", "filing_date": date(2019, 1, 24), "filing_type": "FinancialResults"},
            {"news_id": "YES-2018-AR",     "subject": "Annual Report 2017-18 - Auditor Report", "filing_date": date(2018, 6, 15), "filing_type": "AnnualReport"},
            {"news_id": "YES-2018Q3-001",  "subject": "Quarterly Financial Results Q3 2018", "filing_date": date(2018, 10, 26), "filing_type": "FinancialResults"},
            {"news_id": "YES-PLEDGE-001",  "subject": "Promoter Shareholding and Pledge Disclosure", "filing_date": date(2018, 11, 10), "filing_type": "SharePledge"},
        ],
        "500209": [  # INFY
            {"news_id": "INFY-2022Q4-001", "subject": "Quarterly Financial Results Q4 2022", "filing_date": date(2022, 4, 13), "filing_type": "FinancialResults"},
            {"news_id": "INFY-2022Q3-001", "subject": "Quarterly Financial Results Q3 2022", "filing_date": date(2022, 1, 12), "filing_type": "FinancialResults"},
            {"news_id": "INFY-2021-AR",    "subject": "Annual Report 2021-22", "filing_date": date(2022, 5, 30), "filing_type": "AnnualReport"},
            {"news_id": "INFY-2021Q4-001", "subject": "Quarterly Financial Results Q4 2021", "filing_date": date(2021, 4, 14), "filing_type": "FinancialResults"},
        ],
    }

    filings = mock_db.get(scrip_code, [])
    # No date filter for mock data — always return full demo history
    return [{**f, "pdf_url": None} for f in filings]


async def fetch_bse_announcements(
    scrip_code: str,
    lookback_days: int = 30,
) -> List[Dict[str, Any]]:
    """
    Fetch filing announcements. Uses mock data for demo companies
    since BSE's public XML endpoint requires authentication.
    """
    mock_data = _get_mock_announcements(scrip_code, lookback_days)
    if mock_data:
        return mock_data

    # Fallback: attempt real BSE API
    url = BSE_XML_URL.format(scrip_code=scrip_code)
    cutoff = date.today() - timedelta(days=lookback_days)
    announcements = []

    async with httpx.AsyncClient(
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bseindia.com/",
        },
        follow_redirects=True,
    ) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"BSE fetch failed for {scrip_code}: {e}")
            return []

        try:
            root = etree.fromstring(resp.content)
        except etree.XMLSyntaxError as e:
            logger.error(f"XML parse failed for {scrip_code}: {e}")
            return []

        for row in root.findall(".//row"):
            news_id  = (row.findtext("NewsID") or "").strip()
            subject  = (row.findtext("NewsHeadline") or row.findtext("NEWSHEADLINE") or "").strip()
            date_str = (row.findtext("NewsDate") or row.findtext("NEWSDATE") or "").strip()
            attach   = (row.findtext("AttachmentName") or "").strip()

            if not news_id or not date_str:
                continue

            filing_date = _parse_bse_date(date_str)
            if not filing_date or filing_date < cutoff:
                continue

            pdf_url = (
                f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{attach}"
                if attach else None
            )
            announcements.append({
                "news_id": news_id,
                "subject": subject,
                "filing_date": filing_date,
                "pdf_url": pdf_url,
                "filing_type": _classify_filing(subject),
            })

    return announcements


async def download_pdf(pdf_url: str, save_path: Path) -> bool:
    await asyncio.sleep(random.uniform(3.0, 8.0))
    save_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        try:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            save_path.write_bytes(resp.content)
            return True
        except Exception as e:
            logger.error(f"PDF download failed {pdf_url}: {e}")
            return False


async def scrape_company_filings(
    db: AsyncSession,
    bse_code: str,
    lookback_days: int = 30,
) -> Dict[str, int]:
    scrip_code = DEMO_COMPANIES.get(bse_code.upper(), bse_code)
    announcements = await fetch_bse_announcements(scrip_code, lookback_days)
    logger.info(f"{bse_code}: {len(announcements)} announcements found")

    new_count = 0
    downloaded_count = 0

    for ann in announcements:
        dedup_hash = _make_dedup_hash(str(ann["filing_date"]), ann["subject"], bse_code)

        existing = await db.execute(
            select(Filing).where(Filing.dedup_hash == dedup_hash)
        )
        if existing.scalar_one_or_none():
            continue

        pdf_path = None
        if ann["pdf_url"]:
            year = ann["filing_date"].year
            safe_id = ann["news_id"].replace("/", "_")
            local_path = PDF_BASE_DIR / bse_code.upper() / str(year) / f"{safe_id}.pdf"
            success = await download_pdf(ann["pdf_url"], local_path)
            if success:
                pdf_path = str(local_path)
                downloaded_count += 1

        filing = Filing(
            company_bse_code=bse_code.upper(),
            bse_news_id=ann["news_id"],
            filing_type=ann["filing_type"],
            subject=ann["subject"],
            filing_date=ann["filing_date"],
            pdf_path=pdf_path,
            source_url=ann["pdf_url"],
            extraction_status="pending",
            dedup_hash=dedup_hash,
        )
        db.add(filing)
        new_count += 1

    if new_count:
        await db.commit()

    return {"found": len(announcements), "new": new_count, "downloaded": downloaded_count}