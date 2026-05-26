import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from rapidfuzz import fuzz
from typing import List, Dict, Any, Optional

from backend.models import Client, Entity, EntityAlias, Transaction, Invoice

logger = logging.getLogger(__name__)

# Lazy load sentence-transformers
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"Failed to load sentence-transformers: {e}. Fallback to fuzzy string matching.")
            _model = False
    return _model


def compute_cosine_similarity(emb1, emb2) -> float:
    try:
        import numpy as np
        dot_product = np.dot(emb1, emb2)
        norm_a = np.linalg.norm(emb1)
        norm_b = np.linalg.norm(emb2)
        return float(dot_product / (norm_a * norm_b))
    except Exception:
        return 0.0


class EntityResolutionPipeline:
    """
    Entity Resolution Pipeline for resolving clients and vendors across various data sources.
    Uses GSTIN, RapidFuzz string matching, and sentence-transformers embeddings.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_client(self, client_name: str, gstin: Optional[str] = None, entity_type: str = "company") -> Entity:
        """
        Resolves a client name to a canonical Entity.
        Saves new entities and aliases as needed.
        """
        # Pass 1: Authoritative match on GSTIN (if present)
        if gstin:
            stmt = select(Entity).where(Entity.gstin == gstin)
            res = await self.db.execute(stmt)
            entity = res.scalars().first()
            if entity:
                # Add alias if it's new
                await self._add_alias_if_needed(entity, client_name)
                return entity

        # Pass 2: Exact or fuzzy match on aliases/names in DB
        # Retrieve all entities of the same type
        stmt = select(Entity).where(Entity.entity_type == entity_type)
        res = await self.db.execute(stmt)
        all_entities = res.scalars().all()

        # Check for matches
        for entity in all_entities:
            # Check all aliases of this entity
            aliases = entity.aliases or []
            aliases.append(entity.canonical_name)
            
            for alias in aliases:
                # Company fuzzy string matching
                if entity_type == "company":
                    if fuzz.token_sort_ratio(client_name.lower(), alias.lower()) >= 85.0:
                        await self._add_alias_if_needed(entity, client_name)
                        return entity
                # Person fuzzy string matching (or fallback)
                elif entity_type == "person":
                    model = get_embedding_model()
                    if model:
                        try:
                            # Use sentence embeddings
                            embs = model.encode([client_name, alias])
                            sim = compute_cosine_similarity(embs[0], embs[1])
                            if sim >= 0.85:
                                await self._add_alias_if_needed(entity, client_name)
                                return entity
                        except Exception as e:
                            logger.error(f"Embedding match failed: {e}")
                    
                    # Fallback to token sort ratio if model is not loaded or fails
                    if fuzz.token_sort_ratio(client_name.lower(), alias.lower()) >= 85.0:
                        await self._add_alias_if_needed(entity, client_name)
                        return entity

        # Create a new canonical entity if no match found
        new_entity = Entity(
            canonical_name=client_name,
            entity_type=entity_type,
            gstin=gstin,
            aliases=[client_name]
        )
        self.db.add(new_entity)
        await self.db.flush()

        alias_entry = EntityAlias(entity_id=new_entity.id, alias=client_name)
        self.db.add(alias_entry)
        await self.db.flush()

        return new_entity

    async def _add_alias_if_needed(self, entity: Entity, alias: str):
        if not entity.aliases:
            entity.aliases = []
        if alias not in entity.aliases:
            entity.aliases.append(alias)
            self.db.add(entity)
            
            # Check if alias exists in EntityAlias table
            stmt = select(EntityAlias).where(EntityAlias.alias == alias)
            res = await self.db.execute(stmt)
            existing_alias = res.scalars().first()
            if not existing_alias:
                new_alias = EntityAlias(entity_id=entity.id, alias=alias)
                self.db.add(new_alias)
            await self.db.flush()

    async def update_client_metrics(self, business_id: int):
        """
        Computes and updates clients total_revenue_share and avg_payment_delay_days in the DB.
        """
        # 1. Compute total revenue of the business from all inflow transactions
        stmt_rev = select(func.sum(Transaction.amount)).where(
            Transaction.business_id == business_id,
            Transaction.direction == "in"
        )
        res_rev = await self.db.execute(stmt_rev)
        total_revenue = float(res_rev.scalar() or 0.0)

        if total_revenue <= 0.0:
            return

        # 2. Get all clients of the business
        stmt_clients = select(Client).where(Client.business_id == business_id)
        res_clients = await self.db.execute(stmt_clients)
        clients = res_clients.scalars().all()

        for client in clients:
            # 2.1 Calculate total revenue from this client
            stmt_client_rev = select(func.sum(Transaction.amount)).where(
                Transaction.business_id == business_id,
                Transaction.direction == "in",
                Transaction.counterparty_id == client.id
            )
            res_client_rev = await self.db.execute(stmt_client_rev)
            client_revenue = float(res_client_rev.scalar() or 0.0)
            
            client.total_revenue_share = round((client_revenue / total_revenue) * 100.0, 2)

            # 2.2 Calculate average payment delay (paid_date - due_date) where status is paid
            stmt_delay = select(Invoice.paid_date, Invoice.due_date).where(
                Invoice.business_id == business_id,
                Invoice.client_id == client.id,
                Invoice.status == "paid",
                Invoice.paid_date != None
            )
            res_delay = await self.db.execute(stmt_delay)
            paid_invoices = res_delay.all()

            if paid_invoices:
                total_delay = 0
                for paid_date, due_date in paid_invoices:
                    delay = (paid_date - due_date).days
                    total_delay += max(0, delay)  # only count actual delays
                client.avg_payment_delay_days = int(total_delay / len(paid_invoices))
            else:
                client.avg_payment_delay_days = 0

            self.db.add(client)

        await self.db.commit()
