from datetime import date, timedelta
from typing import List, Dict, Any
from rapidfuzz import fuzz


def _get_party_name(tx: Dict[str, Any]) -> str:
    """Extracts party name from a transaction dict, supporting multiple field name conventions."""
    return tx.get("counterparty_name") or tx.get("raw_description") or ""


def are_counterparties_similar(name1: str, name2: str, threshold: float = 0.8) -> bool:
    """
    Checks if two counterparty names are similar using token sort ratio.
    """
    if not name1 or not name2:
        return name1 == name2

    n1 = name1.strip().lower()
    n2 = name2.strip().lower()

    if n1 == n2 or n1 in n2 or n2 in n1:
        return True

    score = fuzz.token_sort_ratio(n1, n2) / 100.0
    return score >= threshold


def deduplicate_transactions(transactions: List[Dict[str, Any]], existing_txs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates a new batch of parsed transactions against existing ones.
    Checks:
      1. Date window within ±2 days.
      2. Exact or near-exact amount (within 0.05 margin).
      3. Direction match.
      4. Counterparty name similarity (or both null).
    Supports both `counterparty_name` and `raw_description` field name conventions.
    """
    deduplicated = []

    for new_tx in transactions:
        is_duplicate = False
        new_date = new_tx["date"]
        new_amount = float(new_tx["amount"])
        new_direction = new_tx["direction"]
        new_party = _get_party_name(new_tx)

        for ext_tx in existing_txs:
            ext_date = ext_tx["date"]
            ext_amount = float(ext_tx["amount"])
            ext_direction = ext_tx["direction"]
            ext_party = _get_party_name(ext_tx)

            if new_direction != ext_direction:
                continue

            if abs((new_date - ext_date).days) > 2:
                continue

            if abs(new_amount - ext_amount) > 0.05:
                continue

            if new_party or ext_party:
                if not are_counterparties_similar(new_party, ext_party):
                    continue

            is_duplicate = True
            break

        if not is_duplicate:
            deduplicated.append(new_tx)

    return deduplicated

