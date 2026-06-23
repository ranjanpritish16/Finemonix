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

    DATE_HEADERS = ["date", "txn date", "transaction date", "value date", "post date", "time"]
    DESC_HEADERS = ["description", "narration", "remarks", "particulars", "transaction remarks", "details", "chq/ref no.", "ref no", "reference"]
    DEBIT_HEADERS = ["debit", "withdrawal", "dr", "debit amount", "withdrawals"]
    CREDIT_HEADERS = ["credit", "deposit", "cr", "credit amount", "deposits"]
    AMOUNT_HEADERS = ["amount", "txn amount", "transaction amount", "amount (inr)"]
    BALANCE_HEADERS = ["balance", "bal", "running balance", "balance (inr)", "closing balance"]

    def __init__(self, csv_content: str):
        self.csv_content = csv_content

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parses CSV bank statement content and returns normalized transaction records.
        """
        raw_lines = self.csv_content.strip().split("\n")
        lines = [line.strip() for line in raw_lines if line.strip()]
        if not lines:
            return []

        # Try to find the header row
        header_idx, headers = self._find_header_row(lines)
        
        mapping = {}
        data_start_idx = 0

        if header_idx != -1 and headers:
            mapping = self._detect_columns(headers)
            data_start_idx = header_idx + 1
        
        # Fallback: if headers not found or missing required ones, try heuristic column detection
        if header_idx == -1 or mapping.get("date") is None or mapping.get("desc") is None:
            mapping, data_start_idx = self._heuristic_column_detection(lines)
            
            if mapping.get("date") is None or mapping.get("desc") is None:
                first_few = "\\n".join(lines[:3])
                raise ValueError(f"Could not auto-detect CSV columns. First rows:\\n{first_few}")

        reader = csv.reader(lines[data_start_idx:])
        transactions = []

        for row in reader:
            if not row or len(row) < 2:
                continue
            
            if all(cell.strip() == "" for cell in row):
                continue

            try:
                date_str = row[mapping["date"]].strip() if mapping.get("date") is not None and mapping["date"] < len(row) else ""
                desc = row[mapping["desc"]].strip() if mapping.get("desc") is not None and mapping["desc"] < len(row) else ""
                
                if not date_str or date_str.lower() in ["total", "summary", "opening balance"]:
                    continue

                # Try parsing date, if it fails completely, skip row
                try:
                    tx_date = self._parse_date(date_str)
                except Exception:
                    continue
                
                amount = 0.0
                direction = "in"

                if mapping.get("debit") is not None and mapping.get("credit") is not None:
                    debit_str = row[mapping["debit"]].strip() if mapping["debit"] < len(row) else ""
                    credit_str = row[mapping["credit"]].strip() if mapping["credit"] < len(row) else ""
                    
                    debit_val = self._clean_amount(debit_str)
                    credit_val = self._clean_amount(credit_str)

                    if debit_val > 0:
                        amount = debit_val
                        direction = "out"
                    elif credit_val > 0:
                        amount = credit_val
                        direction = "in"
                    else:
                        continue

                elif mapping.get("amount") is not None:
                    amount_str = row[mapping["amount"]].strip() if mapping["amount"] < len(row) else ""
                    is_negative = "-" in amount_str or "dr" in amount_str.lower()
                    
                    val = self._clean_amount(amount_str)
                    if val == 0.0:
                        continue
                        
                    amount = val
                    direction = "out" if is_negative else "in"
                else:
                    continue

                category = "General"
                lower_desc = desc.lower()
                if "salary" in lower_desc or "payroll" in lower_desc:
                    category = "Salary"
                elif "rent" in lower_desc:
                    category = "Rent"
                elif "electricity" in lower_desc or "bill" in lower_desc or "power" in lower_desc:
                    category = "Electricity"
                elif "upi" in lower_desc or "netbanking" in lower_desc or "imps" in lower_desc or "neft" in lower_desc or "rtgs" in lower_desc:
                    category = "Transfer"
                elif "charge" in lower_desc or "interest" in lower_desc or "fee" in lower_desc:
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

            except Exception:
                continue

        return transactions

    def _heuristic_column_detection(self, lines: List[str]) -> Tuple[Dict[str, int], int]:
        """
        Fallback method that scans rows for data types to guess column indices.
        Returns (mapping, data_start_idx)
        """
        for i, line in enumerate(lines[:30]):
            try:
                row = next(csv.reader([line]))
                if len(row) < 3:
                    continue
                
                # Check if this row looks like a valid data row
                mapping = {}
                
                # 1. Find Date column (usually 0 or 1)
                for col_idx, cell in enumerate(row):
                    cell = cell.strip()
                    if not cell: continue
                    try:
                        self._parse_date(cell)
                        mapping["date"] = col_idx
                        break
                    except Exception:
                        pass
                
                # 2. Find Description (longest string that's not a number/date)
                max_len = -1
                desc_idx = -1
                for col_idx, cell in enumerate(row):
                    if mapping.get("date") == col_idx: continue
                    cell = cell.strip()
                    if not cell: continue
                    # Not purely numeric
                    if not re.match(r'^[-+]?[\d.,]+$', cell):
                        if len(cell) > max_len:
                            max_len = len(cell)
                            desc_idx = col_idx
                if desc_idx != -1:
                    mapping["desc"] = desc_idx

                # 3. Find Amount(s)
                num_cols = []
                for col_idx, cell in enumerate(row):
                    if col_idx in [mapping.get("date"), mapping.get("desc")]: continue
                    cell = cell.strip()
                    if re.match(r'^[-+]?[\d.,]+$', cell) and self._clean_amount(cell) >= 0:
                        num_cols.append(col_idx)
                
                if len(num_cols) >= 3:
                    # Likely: Debit, Credit, Balance
                    mapping["debit"] = num_cols[0]
                    mapping["credit"] = num_cols[1]
                    mapping["balance"] = num_cols[2]
                elif len(num_cols) == 2:
                    # Amount, Balance or Debit, Credit
                    # We'll guess Debit/Credit if they are adjacent
                    mapping["debit"] = num_cols[0]
                    mapping["credit"] = num_cols[1]
                elif len(num_cols) == 1:
                    # Just Amount
                    mapping["amount"] = num_cols[0]

                if "date" in mapping and "desc" in mapping and ("amount" in mapping or "debit" in mapping):
                    return mapping, i
            except Exception:
                pass
                
        return {}, 0

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
