import pytest
from datetime import date
from backend.services.tally_parser import TallyParser
from backend.services.gst_parser import GSTParser
from backend.services.bank_parser import BankParser
from backend.services.deduplication import deduplicate_transactions, are_counterparties_similar


def test_tally_parser():
    xml_data = """
    <ENVELOPE>
        <TALLYMESSAGE>
            <LEDGER NAME="Tata Consultancy Services Ltd">
                <PARENT>Sundry Debtors</PARENT>
                <PARTYGSTIN>27AAAAT1111A1Z2</PARTYGSTIN>
            </LEDGER>
            <VOUCHER VOUCHERTYPENAME="Receipt" VOUCHERNUMBER="12" DATE="20241015">
                <PARTYLEDGERNAME>Tata Consultancy Services Ltd</PARTYLEDGERNAME>
                <ISOPTIONAL>No</ISOPTIONAL>
                <ISCANCELLED>No</ISCANCELLED>
                <NARRATION>Payment recd</NARRATION>
                <ALLLEDGERENTRIES.LIST>
                    <AMOUNT>-50000.00</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
            </VOUCHER>
            <VOUCHER VOUCHERTYPENAME="Sales" VOUCHERNUMBER="SAL-01" DATE="20241001">
                <PARTYLEDGERNAME>Tata Consultancy Services Ltd</PARTYLEDGERNAME>
                <ISOPTIONAL>No</ISOPTIONAL>
                <ISCANCELLED>No</ISCANCELLED>
                <EFFECTIVEDATE>20241001</EFFECTIVEDATE>
                <ALLLEDGERENTRIES.LIST>
                    <AMOUNT>50000.00</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
            </VOUCHER>
        </TALLYMESSAGE>
    </ENVELOPE>
    """
    parser = TallyParser(xml_data)
    transactions, invoices, clients = parser.parse()

    assert len(clients) == 1
    assert clients[0]["canonical_name"] == "Tata Consultancy Services Ltd"
    assert clients[0]["gstin"] == "27AAAAT1111A1Z2"

    assert len(transactions) == 1
    assert transactions[0]["amount"] == 50000.0
    assert transactions[0]["direction"] == "in"
    assert transactions[0]["category"] == "Customer Receipt"

    assert len(invoices) == 1
    assert invoices[0]["amount"] == 50000.0
    assert invoices[0]["invoice_type"] == "sales"


def test_gst_parser():
    gstr1_json = """
    {
        "b2b": [
            {
                "ctin": "27AAAAT1111A1Z2",
                "tradeName": "TCS Ltd",
                "inv": [
                    {
                        "inum": "INV-100",
                        "idt": "15-10-2024",
                        "val": 118000.0,
                        "itms": [
                            {
                                "itm_det": {
                                    "txval": 100000.0,
                                    "iamt": 18000.0,
                                    "camt": 0.0,
                                    "samt": 0.0,
                                    "csamt": 0.0
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    parser = GSTParser(gstr1_json)
    invoices, clients = parser.parse(file_type="gstr1")

    assert len(clients) == 1
    assert clients[0]["canonical_name"] == "TCS Ltd"
    assert clients[0]["gstin"] == "27AAAAT1111A1Z2"

    assert len(invoices) == 1
    assert invoices[0]["invoice_number"] == "INV-100"
    assert invoices[0]["amount"] == 118000.0
    assert invoices[0]["taxable_value"] == 100000.0
    assert invoices[0]["tax_amount"] == 18000.0
    assert invoices[0]["direction"] == "in"


def test_bank_parser():
    csv_data = """Transaction Date,Narration,Chq/Ref No.,Value Date,Debit,Credit,Balance
15/10/2024,UPI-SALARY-1234,,15/10/2024,,45000.00,105000.00
16/10/2024,OFFICE RENT HDFC,,16/10/2024,15000.00,,90000.00
"""
    parser = BankParser(csv_data)
    transactions = parser.parse()

    assert len(transactions) == 2
    assert transactions[0]["amount"] == 45000.0
    assert transactions[0]["direction"] == "in"
    assert transactions[0]["category"] == "Salary"

    assert transactions[1]["amount"] == 15000.0
    assert transactions[1]["direction"] == "out"
    assert transactions[1]["category"] == "Rent"


def test_deduplication():
    new_txs = [
        {"date": date(2024, 10, 15), "amount": 50000.0, "direction": "in", "counterparty_name": "TCS Ltd"},
        {"date": date(2024, 10, 20), "amount": 10000.0, "direction": "out", "counterparty_name": "Office Depot"}
    ]

    existing_txs = [
        # Matches the first transaction within ±2 days and close amount
        # Uses `counterparty_name` field (same as new_txs)
        {"date": date(2024, 10, 16), "amount": 50000.0, "direction": "in", "counterparty_name": "TCS Ltd"}
    ]

    deduped = deduplicate_transactions(new_txs, existing_txs)

    assert len(deduped) == 1
    assert deduped[0]["counterparty_name"] == "Office Depot"
    assert deduped[0]["amount"] == 10000.0


def test_deduplication_with_raw_description():
    """Test dedup works when existing txs use raw_description instead of counterparty_name."""
    new_txs = [
        {"date": date(2024, 10, 15), "amount": 75000.0, "direction": "in", "counterparty_name": "Infosys Technologies"},
    ]
    existing_txs = [
        {"date": date(2024, 10, 15), "amount": 75000.0, "direction": "in", "raw_description": "Infosys Technologies"}
    ]
    deduped = deduplicate_transactions(new_txs, existing_txs)
    # Should be detected as duplicate
    assert len(deduped) == 0


def test_counterparty_similarity():
    # Similar names (partial abbreviation and slight variation)
    assert are_counterparties_similar("Infosys Technologies Ltd", "Infosys Technologies") is True
    # Exact match
    assert are_counterparties_similar("TCS Ltd", "TCS Ltd") is True
    # Contains check — one name is a substring of the other
    assert are_counterparties_similar("Tata Motors", "Tata Motors Limited") is True
    # Completely different names
    assert are_counterparties_similar("Reliance Industries", "Wipro Technologies") is False

