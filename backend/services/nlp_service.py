# backend/services/nlp_service.py

import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import spacy

logger = logging.getLogger(__name__)

# Load once at module level — en_core_web_sm is already installed
_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
        _add_custom_patterns(_nlp)
    return _nlp


# ------------------------------------------------------------------
# Custom entity patterns for financial domain
# ------------------------------------------------------------------

AUDIT_OPINION_PATTERNS = [
    r"qualified opinion",
    r"adverse opinion",
    r"disclaimer of opinion",
    r"emphasis of matter",
    r"going concern",
    r"material weakness",
    r"significant doubt",
    r"modified opinion",
]

REGULATORY_TERM_PATTERNS = [
    r"rbi (?:directive|notice|inquiry|circular|regulation)",
    r"sebi (?:notice|inquiry|order|regulation|show cause)",
    r"nclt",
    r"insolvency (?:proceedings|petition|resolution)",
    r"enforcement directorate",
    r"income tax (?:notice|raid|survey|demand)",
    r"forensic audit",
    r"special audit",
    r"cbi (?:inquiry|investigation|raid)",
    r"money laundering",
    r"wilful defaulter",
    r"npa|non.performing asset",
]

PROMOTER_ACTION_PATTERNS = [
    r"promoter.*pledge[ds]?",
    r"pledge.*(?:increased|decreased|created|invoked|released)",
    r"encumber(?:ed|ance)",
    r"promoter.*(?:sold|divested|acquired|transferred) shares",
    r"inter.se transfer",
    r"creeping acquisition",
]


def _add_custom_patterns(nlp):
    """Add a rule-based pipeline component for custom financial entities."""
    from spacy.language import Language
    from spacy.tokens import Span

    if "custom_finance_ner" in nlp.pipe_names:
        return

    @Language.component("custom_finance_ner")
    def custom_finance_ner(doc):
        new_ents = list(doc.ents)
        text_lower = doc.text.lower()

        def _find_spans(patterns: List[str], label: str):
            for pattern in patterns:
                for m in re.finditer(pattern, text_lower):
                    span = doc.char_span(m.start(), m.end(), label=label,
                                        alignment_mode="expand")
                    if span is not None:
                        new_ents.append(span)

        _find_spans(AUDIT_OPINION_PATTERNS, "AUDIT_OPINION")
        _find_spans(REGULATORY_TERM_PATTERNS, "REGULATORY_TERM")
        _find_spans(PROMOTER_ACTION_PATTERNS, "PROMOTER_ACTION")

        # Filter overlaps — keep longest span when they conflict
        new_ents = spacy.util.filter_spans(new_ents)
        doc.ents = new_ents
        return doc

    nlp.add_pipe("custom_finance_ner", last=True)


# ------------------------------------------------------------------
# Ratio extraction via regex
# ------------------------------------------------------------------

RATIO_PATTERNS: Dict[str, List[str]] = {
    "interest_coverage_ratio": [
        r"interest coverage ratio[:\s]+([0-9]+\.?[0-9]*)\s*x?",
        r"icr[:\s]+([0-9]+\.?[0-9]*)\s*x?",
        r"interest coverage[:\s]+([0-9]+\.?[0-9]*)",
    ],
    "debt_to_equity": [
        r"debt.to.equity[:\s]+([0-9]+\.?[0-9]*)",
        r"d/e ratio[:\s]+([0-9]+\.?[0-9]*)",
        r"debt equity ratio[:\s]+([0-9]+\.?[0-9]*)",
    ],
    "promoter_pledge_pct": [
        r"pledge[ds]?\s+([0-9]+\.?[0-9]*)%?\s+(?:of\s+)?(?:promoter|total)",
        r"([0-9]+\.?[0-9]*)%?\s+(?:of\s+)?(?:promoter\s+)?shares?\s+(?:are\s+)?pledge[ds]?",
        r"promoter pledge[:\s]+([0-9]+\.?[0-9]*)%?",
    ],
    "gnpa_pct": [
        r"gnpa[:\s]+([0-9]+\.?[0-9]*)%?",
        r"gross npa[:\s]+([0-9]+\.?[0-9]*)%?",
        r"gross non.performing assets?[:\s]+([0-9]+\.?[0-9]*)%?",
    ],
    "revenue_growth_pct": [
        r"revenue (?:grew|increased|declined|decreased)(?: by)?\s+([0-9]+\.?[0-9]*)%?",
        r"(?:revenue|income) growth[:\s]+([0-9]+\.?[0-9]*)%?",
    ],
    "current_ratio": [
        r"current ratio[:\s]+([0-9]+\.?[0-9]*)",
    ],
    "return_on_equity": [
        r"return on equity[:\s]+([0-9]+\.?[0-9]*)%?",
        r"roe[:\s]+([0-9]+\.?[0-9]*)%?",
    ],
}


def extract_ratios(text: str) -> Dict[str, Optional[float]]:
    """Extract financial ratios from filing text using regex patterns."""
    text_lower = text.lower()
    results: Dict[str, Optional[float]] = {}

    for ratio_name, patterns in RATIO_PATTERNS.items():
        value = None
        for pattern in patterns:
            m = re.search(pattern, text_lower)
            if m:
                try:
                    value = float(m.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        results[ratio_name] = value

    return results


# ------------------------------------------------------------------
# Main NLP pipeline
# ------------------------------------------------------------------

def run_nlp_pipeline(text: str) -> Dict[str, Any]:
    """
    Run the full NLP pipeline on filing text.
    Returns a dict ready to be stored in FilingNlpResult.
    """
    if not text or len(text.strip()) < 50:
        return {
            "entities": [],
            "extracted_ratios": {},
            "audit_opinions": [],
            "regulatory_terms": [],
            "promoter_actions": [],
            "nlp_status": "skipped_empty",
            "spacy_model": "en_core_web_sm",
        }

    nlp = get_nlp()

    # Truncate to spaCy's max length (1M chars) — filings rarely exceed this
    doc = nlp(text[:900_000])

    # Collect all entities
    entities = [
        {
            "text": ent.text.strip(),
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
        }
        for ent in doc.ents
        if ent.text.strip()
    ]

    # Split by custom label
    audit_opinions = [
        e["text"] for e in entities if e["label"] == "AUDIT_OPINION"
    ]
    regulatory_terms = [
        e["text"] for e in entities if e["label"] == "REGULATORY_TERM"
    ]
    promoter_actions = [
        e["text"] for e in entities if e["label"] == "PROMOTER_ACTION"
    ]

    # Extract financial ratios
    extracted_ratios = extract_ratios(text)

    return {
        "entities": entities,
        "extracted_ratios": extracted_ratios,
        "audit_opinions": audit_opinions,
        "regulatory_terms": regulatory_terms,
        "promoter_actions": promoter_actions,
        "nlp_status": "processed",
        "spacy_model": "en_core_web_sm",
    }