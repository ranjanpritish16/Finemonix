import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
import re
from typing import List, Dict, Any, Tuple


class TallyParser:
    """
    Parser for Tally ERP 9 / TallyPrime XML exports.
    Extracts transactions, invoices, and client lists from LEDGER and VOUCHER nodes.
    """

    def __init__(self, xml_content: str):
        self.xml_content = xml_content
        self.root = None

    def parse(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parses Tally XML data.
        Returns:
            Tuple of (transactions, invoices, clients)
        """
        try:
            self.root = ET.fromstring(self.xml_content)
        except Exception as e:
            # Try to clean up encoding issues common in Tally XML exports
            cleaned = self.xml_content.strip()
            # Remove XML declaration if it has encoding mismatch
            cleaned = re.sub(r'<\?xml.*?\?>', '', cleaned)
            try:
                # Add a wrapper root if there are multiple root tags
                self.root = ET.fromstring(f"<ROOT>{cleaned}</ROOT>")
            except Exception as inner_e:
                raise ValueError(f"Failed to parse XML content: {inner_e}")

        clients = self._extract_clients()
        transactions, invoices = self._extract_vouchers()

        return transactions, invoices, clients

    def _clean_amount(self, amt_str: str) -> float:
        """
        Cleans amount string and handles multi-currency entries.
        Converts all currencies to INR.
        """
        if not amt_str:
            return 0.0
        
        # Remove commas
        cleaned = amt_str.replace(",", "")
        
        # Multi-currency detection, e.g., "$ 100", "USD 150 = INR 12000" or similar
        # Standard format in Tally: "-$ 100.00" or "100.00"
        # If there is an '=' sign, Tally has pre-converted it, let's extract the INR value.
        if "=" in cleaned:
            parts = cleaned.split("=")
            # Try to grab the INR part
            for part in parts:
                if "INR" in part or "Rs" in part:
                    match = re.search(r'[-+]?\d*\.\d+|\d+', part)
                    if match:
                        return float(match.group())
            cleaned = parts[-1]  # fallback to last part

        # If no explicit conversion was done but we see a foreign currency symbol,
        # apply a hardcoded exchange rate multiplier for common currencies.
        multiplier = 1.0
        if "$" in cleaned or "USD" in cleaned:
            multiplier = 83.0
        elif "€" in cleaned or "EUR" in cleaned:
            multiplier = 90.0
        elif "£" in cleaned or "GBP" in cleaned:
            multiplier = 105.0

        # Find first decimal or integer number
        match = re.search(r'[-+]?\d*\.\d+|\d+', cleaned)
        if match:
            val = float(match.group())
            # In Tally, debit amounts are sometimes negative, credit positive, or vice-versa
            # We want the absolute value and will determine direction from voucher type
            return abs(val * multiplier)
        
        return 0.0

    def _parse_date(self, date_str: str) -> date:
        """
        Parses Tally date format, which is typically YYYYMMDD.
        """
        if not date_str:
            return date.today()
        
        cleaned = date_str.strip()
        # Remove non-digits
        cleaned = re.sub(r'\D', '', cleaned)
        
        if len(cleaned) == 8:
            try:
                return datetime.strptime(cleaned, "%Y%m%d").date()
            except ValueError:
                pass
        
        try:
            return datetime.strptime(cleaned[:8], "%Y%m%d").date()
        except Exception:
            return date.today()

    def _extract_clients(self) -> List[Dict[str, Any]]:
        """
        Extracts master client details from LEDGER nodes where parent group is Sundry Debtors or Sundry Creditors.
        """
        clients = []
        # Find all LEDGER nodes
        # Tally wraps them under <TALLYMESSAGE> or directly under root
        ledgers = self.root.findall(".//LEDGER")
        
        for ledger in ledgers:
            name = ledger.get("NAME") or ledger.findtext("NAME")
            if not name:
                continue
                
            parent = ledger.findtext("PARENT") or ""
            # Sundry Debtors represent clients/receivables, Sundry Creditors represent vendors/payables
            is_client = "Sundry Debtors" in parent
            is_vendor = "Sundry Creditors" in parent
            
            if is_client or is_vendor:
                gstin = ledger.findtext("PARTYGSTIN") or ledger.findtext("GSTIN") or None
                if gstin:
                    gstin = gstin.strip()
                    
                clients.append({
                    "canonical_name": name.strip(),
                    "gstin": gstin,
                    "is_vendor": is_vendor,
                    "ledger_group": parent.strip(),
                })
                
        return clients

    def _extract_vouchers(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extracts transactions and invoices from VOUCHER nodes.
        Handles VOUCHER types: RECEIPT, PAYMENT, JOURNAL, CONTRA, SALESVOUCHER, PURCHASEVOUCHER.
        """
        transactions = []
        invoices = []
        
        vouchers = self.root.findall(".//VOUCHER")
        for voucher in vouchers:
            # Check edge case: Cancelled or optional vouchers
            is_optional = voucher.findtext("ISOPTIONAL") or ""
            is_cancelled = voucher.findtext("ISCANCELLED") or ""
            if is_optional.lower() == "yes" or is_cancelled.lower() == "yes":
                continue

            # Tally exports VOUCHERTYPENAME and DATE as XML attributes OR child elements
            vtype = (voucher.get("VOUCHERTYPENAME") or voucher.findtext("VOUCHERTYPENAME") or "").strip().upper()
            date_str = voucher.get("DATE") or voucher.get("date") or voucher.findtext("DATE")
            vdate = self._parse_date(date_str)
            
            party_name = voucher.findtext("PARTYLEDGERNAME") or ""
            raw_desc = voucher.findtext("NARRATION") or ""
            
            # Extract voucher number as reference (also can be an attribute)
            vnum = voucher.get("VOUCHERNUMBER") or voucher.findtext("VOUCHERNUMBER") or ""

            # Determine Amount and Direction
            # Vouchers contain LEDGERENTRIES.LIST or ALLLEDGERENTRIES.LIST
            entries = voucher.findall(".//ALLLEDGERENTRIES.LIST") or voucher.findall(".//LEDGERENTRIES.LIST")
            
            total_amount = 0.0
            # Try to get overall voucher amount or sum ledger entries
            for entry in entries:
                amount_text = entry.findtext("AMOUNT")
                if amount_text:
                    total_amount += self._clean_amount(amount_text)
            
            # If total_amount is 0, check parent VOUCHER nodes for an amount
            if total_amount == 0.0:
                amount_text = voucher.findtext("AMOUNT")
                if amount_text:
                    total_amount = self._clean_amount(amount_text)

            if total_amount == 0.0:
                continue

            # Standardize Transaction schema:
            # RECEIPT, PAYMENT, JOURNAL, CONTRA
            is_txn = any(t in vtype for t in ["RECEIPT", "PAYMENT", "JOURNAL", "CONTRA"])
            # SALESVOUCHER, PURCHASEVOUCHER (or SALES, PURCHASE)
            is_invoice = any(t in vtype for t in ["SALES", "PURCHASE", "INVOICE"])

            direction = "in"
            if any(t in vtype for t in ["PAYMENT", "PURCHASE", "DEBITNOTE"]):
                direction = "out"

            category = "General"
            if "RECEIPT" in vtype:
                category = "Customer Receipt"
            elif "PAYMENT" in vtype:
                category = "Vendor Payment"
            elif "JOURNAL" in vtype:
                category = "Adjustment Journal"
            elif "CONTRA" in vtype:
                category = "Bank Transfer"
            elif "SALES" in vtype:
                category = "Sales Revenue"
            elif "PURCHASE" in vtype:
                category = "Purchase Expense"

            if is_txn:
                transactions.append({
                    "date": vdate,
                    "amount": total_amount,
                    "direction": direction,
                    "category": category,
                    "counterparty_name": party_name.strip() if party_name else None,
                    "source": "tally",
                    "raw_description": f"Voucher: {vtype} #{vnum}. Narration: {raw_desc}".strip(),
                })

            if is_invoice:
                # Due date for sales/purchase can be set to issue date + 30 days default
                # or parsed from bill allocation details if present.
                due_date = vdate + timedelta(days=30)
                bill_date = voucher.findtext("EFFECTIVEDATE")
                if bill_date:
                    vdate = self._parse_date(bill_date)
                    due_date = vdate + timedelta(days=30)

                invoices.append({
                    "amount": total_amount,
                    "issue_date": vdate,
                    "due_date": due_date,
                    "status": "pending",
                    "counterparty_name": party_name.strip() if party_name else None,
                    "invoice_type": "sales" if direction == "in" else "purchase",
                })

        # To avoid circular import, we helper format due date
        return transactions, invoices
