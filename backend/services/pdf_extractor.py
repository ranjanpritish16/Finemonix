# backend/services/pdf_extractor.py

import logging
import os
from pathlib import Path
from typing import Tuple, Optional

import pdfplumber
import pytesseract
from PIL import Image, ImageFilter, ImageOps
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

# Point pytesseract to Tesseract binary on Windows
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Minimum characters per page to consider a PDF as text-layer
TEXT_CHARS_THRESHOLD = 100


def is_scanned_pdf(file_path: str) -> bool:
    """
    Returns True if the PDF is a scanned image (no text layer).
    Heuristic: average characters per page < TEXT_CHARS_THRESHOLD.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                return True
            total_chars = sum(
                len(page.extract_text() or "") for page in pdf.pages
            )
            avg_chars = total_chars / len(pdf.pages)
            return avg_chars < TEXT_CHARS_THRESHOLD
    except Exception as e:
        logger.warning(f"PDF type detection failed for {file_path}: {e}")
        return False


def extract_text_pdf(file_path: str) -> str:
    """
    Extract text from a text-layer PDF using pdfplumber.
    Handles multi-column layouts by sorting text blocks.
    Strips repeated headers/footers.
    """
    pages_text = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract words with positions for layout-aware ordering
                words = page.extract_words(
                    x_tolerance=3,
                    y_tolerance=3,
                    keep_blank_chars=False,
                )
                if not words:
                    continue

                # Sort by top (y) then left (x) for reading order
                words.sort(key=lambda w: (round(w["top"] / 10) * 10, w["x0"]))
                page_text = " ".join(w["text"] for w in words)
                pages_text.append(page_text)

    except Exception as e:
        logger.error(f"Text PDF extraction failed for {file_path}: {e}")
        return ""

    full_text = "\n\n".join(pages_text)
    return _remove_repeated_lines(full_text)


def _preprocess_image(img: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR accuracy:
    - Convert to grayscale
    - Apply Otsu binarization via threshold
    - Mild sharpening
    """
    img = img.convert("L")  # grayscale
    # Otsu-style binarization using point threshold
    img = img.point(lambda x: 0 if x < 140 else 255, "1")
    img = img.convert("RGB")
    img = img.filter(ImageFilter.SHARPEN)
    return img


def extract_ocr_pdf(file_path: str) -> Tuple[str, float]:
    """
    Extract text from a scanned PDF using Tesseract OCR.
    Returns (extracted_text, confidence_score 0-1).
    """
    pages_text = []
    confidence_scores = []

    try:
        images = convert_from_path(
            file_path,
            dpi=300,
            fmt="png",
        )
    except Exception as e:
        logger.error(f"PDF to image conversion failed for {file_path}: {e}")
        return "", 0.0

    for i, img in enumerate(images):
        try:
            processed = _preprocess_image(img)

            # Get OCR data with confidence scores
            data = pytesseract.image_to_data(
                processed,
                lang="eng",
                output_type=pytesseract.Output.DICT,
            )

            # Filter words with confidence > 0
            words = []
            confs = []
            for j, conf in enumerate(data["conf"]):
                if int(conf) > 0:
                    words.append(data["text"][j])
                    confs.append(int(conf))

            if words:
                pages_text.append(" ".join(w for w in words if w.strip()))
            if confs:
                confidence_scores.append(sum(confs) / len(confs))

        except Exception as e:
            logger.warning(f"OCR failed on page {i+1} of {file_path}: {e}")
            continue

    full_text = "\n\n".join(pages_text)
    avg_confidence = (
        sum(confidence_scores) / len(confidence_scores) / 100.0
        if confidence_scores else 0.0
    )

    return full_text, round(avg_confidence, 3)


def _remove_repeated_lines(text: str, threshold: int = 3) -> str:
    """
    Remove lines that appear more than `threshold` times
    (likely headers/footers).
    """
    lines = text.split("\n")
    from collections import Counter
    line_counts = Counter(l.strip() for l in lines if l.strip())
    filtered = [
        line for line in lines
        if not line.strip() or line_counts[line.strip()] <= threshold
    ]
    return "\n".join(filtered)


def extract_filing_text(file_path: str) -> Tuple[str, str, Optional[float]]:
    """
    Main extraction function. Auto-detects PDF type and extracts text.

    Returns:
        (text, extractor_used, ocr_confidence)
        extractor_used: 'pdfplumber' | 'tesseract'
        ocr_confidence: float 0-1 for tesseract, None for pdfplumber
    """
    if not file_path or not Path(file_path).exists():
        logger.warning(f"File not found: {file_path}")
        return "", "none", None

    scanned = is_scanned_pdf(file_path)

    if scanned:
        logger.info(f"Scanned PDF detected: {file_path}")
        text, confidence = extract_ocr_pdf(file_path)
        return text, "tesseract", confidence
    else:
        logger.info(f"Text PDF detected: {file_path}")
        text = extract_text_pdf(file_path)
        return text, "pdfplumber", None


def generate_mock_filing_text(filing_type: str, subject: str, bse_code: str) -> str:
    """
    Generate realistic mock text for demo filings that have no actual PDF.
    Used when pdf_path is None (all mock filings in Day 20).
    """
    templates = {
        "FinancialResults": f"""
BOARD OF DIRECTORS REPORT
{bse_code} LIMITED
QUARTERLY FINANCIAL RESULTS

{subject}

Dear Shareholders,

The Board of Directors hereby presents the financial results for the quarter.

FINANCIAL HIGHLIGHTS:
Revenue from Operations: Rs. 2,450 Crores
Total Expenses: Rs. 2,180 Crores  
EBITDA: Rs. 270 Crores
Interest Coverage Ratio: 1.8x
Debt to Equity Ratio: 3.2
Days Sales Outstanding: 87 days
Promoter Shareholding: 39.5%
Promoter Pledge: 42.3%

Management Discussion:
The company continues to face headwinds in the current macroeconomic environment.
Revenue growth has moderated compared to previous quarters.
We remain committed to our business plan and expect improvement in coming quarters.
Interest costs have increased due to rising benchmark rates.
Collections from borrowers have shown some stress in select segments.

For and on behalf of the Board of Directors,
{bse_code} Limited
""",
        "AnnualReport": f"""
ANNUAL REPORT
{bse_code} LIMITED

{subject}

MANAGEMENT DISCUSSION AND ANALYSIS

Dear Members,

Your Directors present the Annual Report of the Company.

BUSINESS OVERVIEW:
The year under review witnessed significant challenges across the financial sector.
The company's loan book grew by 18% year on year.
Asset quality remained under pressure with GNPA at 2.8%.

AUDITOR'S REPORT:
We draw attention to Note 32 of the financial statements regarding 
certain borrower accounts where the management has made estimates
that differ from our assessment. We have issued a qualified opinion
on these specific matters.

KEY FINANCIAL RATIOS:
Interest Coverage Ratio: 1.4x
Current Ratio: 0.82
Debt to Equity: 4.1
Promoter Pledge Percentage: 64.2%
Return on Equity: 8.3%

RISK FACTORS:
The company faces concentration risk in certain borrower segments.
Regulatory scrutiny has increased in the NBFC sector.
Liquidity conditions in the market remain tight.

DIRECTORS' RESPONSIBILITY STATEMENT:
The Directors confirm that the financial statements have been prepared
in accordance with applicable accounting standards.
""",
        "SharePledge": f"""
DISCLOSURE UNDER SEBI REGULATIONS
{bse_code} LIMITED

{subject}

Pursuant to Regulation 31 of SEBI (Listing Obligations and Disclosure Requirements) 
Regulations, 2015, we hereby disclose the following:

PROMOTER SHAREHOLDING AND PLEDGE DETAILS:

Total Promoter Holding: 39.21%
Shares Pledged/Encumbered: 64.18% of promoter holding
Change from previous disclosure: +18.3 percentage points

The promoters have pledged additional shares as collateral for 
loans availed from financial institutions.

This disclosure is being made in compliance with applicable SEBI regulations.

For {bse_code} Limited
Company Secretary
""",
        "General": f"""
BSE FILING
{bse_code} LIMITED

{subject}

This filing is submitted pursuant to applicable SEBI regulations
and listing obligations.

The company wishes to inform the Exchange of the following developments:

Regulatory Compliance Update:
The company has received certain queries from regulatory authorities
regarding its operations and financial disclosures.
The company is cooperating fully with all regulatory inquiries.
Management is confident of resolving all matters satisfactorily.

For further information, please contact:
Investor Relations
{bse_code} Limited
""",
    }

    return templates.get(filing_type, templates["General"])