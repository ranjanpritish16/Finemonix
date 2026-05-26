import csv
import io
import re
from datetime import datetime, date
from typing import List, Dict, Any, Tuple


class BankParser:
    """
    Parser for Indian bank CSV statements (SBI, HDFC, ICICI, Axis, Kotak).
    Includes auto-detection of columns (date, narration, debit, credit, balance).
    """

    DATE_HEADERS = ["date", "txn date", "transaction date", "value date", "post date"]
    DESC_HEADERS = ["description", "narration", "remarks", "particulars", "transaction remarks"]
    DEBIT_HEADERS = ["debit", "withdrawal", "dr", "debit amount", "withdrawals"]
    CREDIT_HEADERS = ["credit", "deposit", "cr", "credit amount", "deposits"]
    AMOUNT_HEADERS = ["amount", "txn amount", "transaction amount", "amount (inr)"]
    BALANCE_HEADERS = ["balance", "bal", "running balance", "balance (inr)"]

    def __init__(self, csv_content: str):
        self.csv_content = csv_content

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parses CSV bank statement content and returns normalized transaction records.
        """
        # Strip leading whitespace from each line (handles multiline Python strings in tests)
        raw_lines = self.csv_content.strip().split("\n")
        lines = [line.strip() for line in raw_lines if line.strip()]
        if not lines:
            return []

        # Try to find the header row by skipping preliminary bank info lines
        header_idx, headers = self._find_header_row(lines)
        if header_idx == -1 or not headers:
            raise ValueError("Could not auto-detect CSV header row or columns.")

        # Map header names to roles
        mapping = self._detect_columns(headers)
        # Use `is not None` because column index 0 would be falsy with a simple `if not`
        if mapping.get("date") is None or mapping.get("desc") is None:
            raise ValueError("Could not find required columns (Date and Description).")

        reader = csv.reader(lines[header_idx + 1:])
        transactions = []

        for row in reader:
            if not row or len(row) < 2:
                continue
            
            # Check if row is empty or summary row
            if all(cell.strip() == "" for cell in row):
                continue

            try:
                date_str = row[mapping["date"]].strip()
                desc = row[mapping["desc"]].strip()
                
                # Check for empty dates (sometimes summary footer rows)
                if not date_str or date_str.lower() in ["total", "summary", "opening balance"]:
                    continue

                tx_date = self._parse_date(date_str)
                
                # Amount / Direction parsing
                amount = 0.0
                direction = "in"

                # Case 1: Debit and Credit in separate columns
                if mapping.get("debit") is not None and mapping.get("credit") is not None:
                    debit_str = row[mapping["debit"]].strip()
                    credit_str = row[mapping["credit"]].strip()
                    
                    debit_val = self._clean_amount(debit_str)
                    credit_val = self._clean_amount(credit_str)

                    if debit_val > 0:
                        amount = debit_val
                        direction = "out"
                    elif credit_val > 0:
                        amount = credit_val
                        direction = "in"
                    else:
                        continue  # zero amount or empty

                # Case 2: Single amount column with Dr/Cr sign or negative for debit
                elif mapping.get("amount") is not None:
                    amount_str = row[mapping["amount"]].strip()
                    # Clean sign
                    is_negative = "-" in amount_str or "dr" in amount_str.lower()
                    
                    val = self._clean_amount(amount_str)
                    if val == 0.0:
                        continue
                        
                    amount = val
                    direction = "out" if is_negative else "in"
                else:
                    # No amount column detected, skip
                    continue

                category = "General"
                # Simple keyword categorizer for bank statement narratives
                lower_desc = desc.lower()
                if "salary" in lower_desc or "payroll" in lower_desc:
                    category = "Salary"
                elif "rent" in lower_desc:
                    category = "Rent"
                elif "electricity" in lower_desc or "bill" in lower_desc or "power" in lower_desc:
                    category = "Electricity"
                elif "upi" in lower_desc or "netbanking" in lower_desc:
                    category = "Transfer"
                elif "charge" in lower_desc or "interest" in lower_desc:
                    category = "Bank Charges"
                elif "gst" in lower_desc or "tax" in lower_desc:
                    category = "Taxes"

                transactions.append({
                    "date": tx_date,
                    "amount": amount,
                    "direction": direction,
                    "category": category,
                    "source": "bank",
                    "raw_description": desc,
                })

            except Exception as e:
                # Log parsing failure for individual row, skip it
                continue

        return transactions

    def _find_header_row(self, lines: List[str]) -> Tuple[int, List[str]]:
        """
        Finds the header row index by scanning rows for date and description keywords.
        """
        for i, line in enumerate(lines[:20]):  # look at first 20 lines
            # parse as csv
            row = next(csv.reader([line]))
            cleaned_row = [cell.strip().lower() for cell in row]
            
            # Count matches
            date_matches = any(any(dh in cell for dh in self.DATE_HEADERS) for cell in cleaned_row)
            desc_matches = any(any(desc_h in cell for desc_h in self.DESC_HEADERS) for cell in cleaned_row)
            
            if date_matches and desc_matches:
                return i, [cell.strip() for cell in row]
        return -1, []

    def _detect_columns(self, headers: List[str]) -> Dict[str, int]:
        """
        Detects indices for date, desc, debit, credit, amount, and balance.
        """
        mapping = {}
        headers_lower = [h.lower() for h in headers]

        for i, h in enumerate(headers_lower):
            # Check Date
            if any(dh == h or dh in h for dh in self.DATE_HEADERS):
                if "date" not in mapping:
                    mapping["date"] = i
            # Check Desc
            elif any(dh == h or dh in h for dh in self.DESC_HEADERS):
                if "desc" not in mapping:
                    mapping["desc"] = i
            # Check Debit
            elif any(dh == h or dh in h for dh in self.DEBIT_HEADERS):
                if "debit" not in mapping:
                    mapping["debit"] = i
            # Check Credit
            elif any(dh == h or dh in h for dh in self.CREDIT_HEADERS):
                if "credit" not in mapping:
                    mapping["credit"] = i
            # Check Amount (fallback if separate columns not present)
            elif any(dh == h or dh in h for dh in self.AMOUNT_HEADERS):
                if "amount" not in mapping:
                    mapping["amount"] = i
            # Check Balance
            elif any(dh == h or dh in h for dh in self.BALANCE_HEADERS):
                if "balance" not in mapping:
                    mapping["balance"] = i

        return mapping

    def _clean_amount(self, amt_str: str) -> float:
        """
        Removes commas, symbols, and returns float.
        """
        if not amt_str:
            return 0.0
        cleaned = amt_str.replace(",", "").replace("INR", "").replace("Rs", "").strip()
        # Find floats
        match = re.search(r'[-+]?\d*\.\d+|\d+', cleaned)
        if match:
            return abs(float(match.group()))
        return 0.0

    def _parse_date(self, date_str: str) -> date:
        """
        Handles formats like DD/MM/YYYY, DD-Mon-YYYY, MM/DD/YY.
        """
        date_str = date_str.strip()
        # Common date formats in Indian bank statements
        formats = [
            "%d/%m/%Y",  # 28/12/2023
            "%d-%m-%Y",  # 28-12-2023
            "%d-%b-%Y",  # 28-Dec-2023
            "%d-%b-%y",  # 28-Dec-23
            "%d %b %Y",  # 28 Dec 2023
            "%Y-%m-%d",  # 2023-12-28
            "%m/%d/%y",  # 12/28/23 (US styled sometimes used)
            "%m/%d/%Y",  # 12/28/2023
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Try to parse via regex or custom logic if all failed
        # e.g., "28-12-2023 12:30:00" -> extract date part
        match = re.match(r'^(\d+[-/]\w+[-/]\d+)', date_str)
        if match:
            extracted = match.group(1)
            for fmt in formats:
                try:
                    return datetime.strptime(extracted, fmt).date()
                except ValueError:
                    continue

        return date.today()
