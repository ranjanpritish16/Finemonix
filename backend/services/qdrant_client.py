# backend/services/qdrant_client.py

from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue,
)
from backend.config import get_settings

COLLECTION_NAME = "filings_text"
VECTOR_DIM = 384          # all-MiniLM-L6-v2 output dimension
DISTANCE = Distance.COSINE


class QdrantFilingsClient:
    """
    Wrapper for Qdrant operations on the filings_text collection.
    """

    def __init__(self, url: str):
        self._client = QdrantClient(url=url)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the collection if it doesn't exist."""
        existing = [c.name for c in self._client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            self._client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=DISTANCE),
            )

    def upsert_embedding(
        self,
        point_id: int,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> None:
        """
        Store a 384-dim embedding with metadata payload.
        payload should include: bse_code, year, quarter, filing_id, filing_type
        """
        self._client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 5,
        bse_code_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find the top-k most similar filings to a query vector.
        Optionally filter by bse_code.
        """
        query_filter = None
        if bse_code_filter:
            query_filter = Filter(
                must=[FieldCondition(
                    key="bse_code",
                    match=MatchValue(value=bse_code_filter),
                )]
            )

        results = self._client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return [
            {"score": r.score, "payload": r.payload, "id": r.id}
            for r in results
        ]

    def get_quarterly_embeddings(
        self,
        bse_code: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all stored embeddings for a company, ordered by quarter.
        Used by the tone drift detector.
        """
        results, _ = self._client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(
                    key="bse_code",
                    match=MatchValue(value=bse_code),
                )]
            ),
            with_vectors=True,
            with_payload=True,
            limit=100,
        )
        return sorted(
            [{"id": r.id, "vector": r.vector, "payload": r.payload} for r in results],
            key=lambda x: (x["payload"].get("year", 0), x["payload"].get("quarter", "")),
        )

    def delete_by_bse_code(self, bse_code: str) -> None:
        """Remove all embeddings for a company (e.g. on re-processing)."""
        self._client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(
                    key="bse_code",
                    match=MatchValue(value=bse_code),
                )]
            ),
        )

    def collection_info(self) -> Dict[str, Any]:
        info = self._client.get_collection(COLLECTION_NAME)
        # vectors_count renamed to points_count in newer qdrant-client versions
        points_count = getattr(info, "points_count", None) or getattr(info, "vectors_count", 0)
        return {
            "name": COLLECTION_NAME,
            "points_count": points_count,
            "dimension": VECTOR_DIM,
            "distance": str(DISTANCE),
        }

# Singleton
_qdrant_client: Optional[QdrantFilingsClient] = None


def get_qdrant_client() -> QdrantFilingsClient:
    global _qdrant_client
    if _qdrant_client is None:
        s = get_settings()
        _qdrant_client = QdrantFilingsClient(s.QDRANT_URL)
    return _qdrant_client