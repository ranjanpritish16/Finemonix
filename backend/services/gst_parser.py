import json
from datetime import datetime, date
from typing import List, Dict, Any, Tuple


class GSTParser:
    """
    Parser for GST JSON files (GSTR-1 and GSTR-2A).
    Extracts invoice records, tax details, and client details.
    """

    def __init__(self, json_content: str):
        self.json_content = json_content

    def parse(self, file_type: str = "gstr1") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parses GST JSON.
        file_type: 'gstr1' (outward/sales) or 'gstr2a' (inward/purchases)
        Returns:
            Tuple of (invoices, clients)
        """
        try:
            data = json.loads(self.json_content)
        except Exception as e:
            raise ValueError(f"Invalid JSON format: {e}")

        invoices = []
        clients_seen = {}

        # Direction mapping: GSTR-1 is outward (sales -> cash in), GSTR-2A is inward (purchases -> cash out)
        direction = "in" if file_type.lower() == "gstr1" else "out"
        
        # Extract GSTR-1 / GSTR-2A sections
        # B2B sections
        b2b_records = data.get("b2b", [])
        for record in b2b_records:
            ctin = record.get("ctin")  # Counterparty GSTIN
            trade_name = record.get("tradeName") or record.get("lnm") or f"GSTIN_{ctin}"
            
            if ctin and ctin not in clients_seen:
                clients_seen[ctin] = {
                    "canonical_name": trade_name.strip(),
                    "gstin": ctin,
                    "is_vendor": (direction == "out"),
                }

            inv_list = record.get("inv", [])
            for inv in inv_list:
                inum = inv.get("inum")  # Invoice number
                idt_str = inv.get("idt")  # Invoice date (DD-MM-YYYY)
                val = float(inv.get("val", 0.0))  # Invoice total value
                
                # Parse date
                issue_date = self._parse_date(idt_str)
                due_date = issue_date + timedelta(days=30) if 'timedelta' in globals() else issue_date
                
                # Extract tax details
                taxable_val = 0.0
                tax_amt = 0.0
                for item in inv.get("itms", []):
                    itm_det = item.get("itm_det", {})
                    taxable_val += float(itm_det.get("txval", 0.0))
                    tax_amt += (
                        float(itm_det.get("iamt", 0.0)) + 
                        float(itm_det.get("camt", 0.0)) + 
                        float(itm_det.get("samt", 0.0)) + 
                        float(itm_det.get("csamt", 0.0))
                    )

                invoices.append({
                    "invoice_number": inum,
                    "gstin": ctin,
                    "counterparty_name": trade_name.strip(),
                    "amount": val,
                    "taxable_value": taxable_val or val,
                    "tax_amount": tax_amt,
                    "issue_date": issue_date,
                    "due_date": issue_date + timedelta(days=30) if 'timedelta' in globals() else issue_date,
                    "direction": direction,
                    "source": "gst",
                    "status": "pending",
                })

        # CDNR (Credit/Debit Notes) sections
        cdnr_records = data.get("cdnr", [])
        for record in cdnr_records:
            ctin = record.get("ctin")
            trade_name = f"GSTIN_{ctin}"
            
            nt_list = record.get("nt", [])
            for note in nt_list:
                nt_num = note.get("nt_num")  # Note number
                nt_dt = note.get("nt_dt")  # Note date
                val = float(note.get("val", 0.0))
                ntty = note.get("ntty")  # C (Credit) or D (Debit)
                
                note_date = self._parse_date(nt_dt)
                
                # Debit note increases the invoice value, Credit note decreases it
                # Direction adjustment
                net_val = val if ntty == "D" else -val
                
                invoices.append({
                    "invoice_number": nt_num,
                    "gstin": ctin,
                    "counterparty_name": trade_name,
                    "amount": net_val,
                    "taxable_value": net_val,
                    "tax_amount": 0.0,
                    "issue_date": note_date,
                    "due_date": note_date,
                    "direction": direction,
                    "source": "gst",
                    "status": "paid",  # Credit/debit notes are applied directly
                })

        # B2CS (B2C Small) sections (typically GSTR-1 only)
        b2cs_records = data.get("b2cs", [])
        for b2cs in b2cs_records:
            sply_ty = b2cs.get("sply_ty", "B2CS")
            val = float(b2cs.get("val", 0.0))
            
            # Since B2CS are daily or monthly aggregates by state, we mock a name
            invoices.append({
                "invoice_number": f"B2CS_{datetime.now().strftime('%Y%m%d%H%M')}_{random_id() if 'random_id' in globals() else 'gen'}",
                "gstin": None,
                "counterparty_name": "B2C Consumer",
                "amount": val,
                "taxable_value": val,
                "tax_amount": 0.0,
                "issue_date": date.today(),
                "due_date": date.today(),
                "direction": direction,
                "source": "gst",
                "status": "paid",
            })

        return invoices, list(clients_seen.values())

    def _parse_date(self, date_str: str) -> date:
        """
        Parses date string formatted as DD-MM-YYYY or DD/MM/YYYY.
        """
        if not date_str:
            return date.today()
        
        date_str = date_str.strip()
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return date.today()


from datetime import timedelta
import random

def random_id():
    return str(random.randint(1000, 9999))
