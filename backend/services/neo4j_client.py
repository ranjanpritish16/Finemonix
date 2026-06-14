# backend/services/neo4j_client.py

from neo4j import GraphDatabase, Driver
from typing import Any, Dict, List, Optional
from backend.config import get_settings


class Neo4jClient:
    """
    Thin wrapper around the official Neo4j Python driver.
    Use as a singleton via get_neo4j_client().
    """

    def __init__(self, uri: str, user: str, password: str):
        self._driver: Driver = GraphDatabase.driver(
            uri, auth=(user, password)
        )

    def close(self):
        self._driver.close()

    def verify_connectivity(self) -> bool:
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Node creation
    # ------------------------------------------------------------------

    def create_company(self, bse_code: str, name: str, cin: str = "") -> None:
        with self._driver.session() as session:
            session.run(
                """
                MERGE (c:Company {bse_code: $bse_code})
                SET c.name = $name, c.cin = $cin
                """,
                bse_code=bse_code, name=name, cin=cin,
            )

    def create_person(self, pan: str, name: str, designation: str = "") -> None:
        with self._driver.session() as session:
            session.run(
                """
                MERGE (p:Person {pan: $pan})
                SET p.name = $name, p.designation = $designation
                """,
                pan=pan, name=name, designation=designation,
            )

    def create_auditor_firm(self, name: str, icai_reg: str = "") -> None:
        with self._driver.session() as session:
            session.run(
                """
                MERGE (a:AuditorFirm {name: $name})
                SET a.icai_reg = $icai_reg
                """,
                name=name, icai_reg=icai_reg,
            )

    # ------------------------------------------------------------------
    # Relationship creation
    # ------------------------------------------------------------------

    def create_director_relationship(
        self,
        bse_code: str,
        pan: str,
        din: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> None:
        with self._driver.session() as session:
            session.run(
                """
                MATCH (c:Company {bse_code: $bse_code})
                MATCH (p:Person {pan: $pan})
                MERGE (c)-[r:IS_DIRECTOR_OF]->(p)
                SET r.din = $din,
                    r.start_date = $start_date,
                    r.end_date = $end_date
                """,
                bse_code=bse_code, pan=pan,
                din=din, start_date=start_date, end_date=end_date,
            )

    def create_audits_relationship(
        self,
        auditor_name: str,
        bse_code: str,
        year: int,
        opinion_type: str = "unmodified",
    ) -> None:
        with self._driver.session() as session:
            session.run(
                """
                MATCH (a:AuditorFirm {name: $auditor_name})
                MATCH (c:Company {bse_code: $bse_code})
                MERGE (a)-[r:AUDITS {year: $year}]->(c)
                SET r.opinion_type = $opinion_type
                """,
                auditor_name=auditor_name, bse_code=bse_code,
                year=year, opinion_type=opinion_type,
            )

    def create_pledge_relationship(
        self,
        pan: str,
        bse_code: str,
        pct_pledged: float,
        date: str,
    ) -> None:
        with self._driver.session() as session:
            session.run(
                """
                MATCH (p:Person {pan: $pan})
                MATCH (c:Company {bse_code: $bse_code})
                MERGE (p)-[r:PLEDGED_SHARES_OF {date: $date}]->(c)
                SET r.pct_pledged = $pct_pledged
                """,
                pan=pan, bse_code=bse_code,
                pct_pledged=pct_pledged, date=date,
            )

    def create_related_party_relationship(
        self,
        from_bse: str,
        to_bse: str,
        txn_type: str,
        amount: float,
        year: int,
    ) -> None:
        with self._driver.session() as session:
            session.run(
                """
                MATCH (c1:Company {bse_code: $from_bse})
                MATCH (c2:Company {bse_code: $to_bse})
                MERGE (c1)-[r:IS_RELATED_PARTY_OF {year: $year}]->(c2)
                SET r.txn_type = $txn_type, r.amount = $amount
                """,
                from_bse=from_bse, to_bse=to_bse,
                txn_type=txn_type, amount=amount, year=year,
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_company_directors(self, bse_code: str) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (c:Company {bse_code: $bse_code})-[r:IS_DIRECTOR_OF]->(p:Person)
                RETURN p.name AS name, p.pan AS pan,
                       p.designation AS designation,
                       r.din AS din, r.start_date AS start_date,
                       r.end_date AS end_date
                """,
                bse_code=bse_code,
            )
            return [dict(record) for record in result]

    def get_pledge_history(self, bse_code: str) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (p:Person)-[r:PLEDGED_SHARES_OF]->(c:Company {bse_code: $bse_code})
                RETURN p.name AS promoter_name, p.pan AS pan,
                       r.pct_pledged AS pct_pledged, r.date AS date
                ORDER BY r.date
                """,
                bse_code=bse_code,
            )
            return [dict(record) for record in result]

    def get_related_parties(self, bse_code: str) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (c:Company {bse_code: $bse_code})-[r:IS_RELATED_PARTY_OF]->(related:Company)
                RETURN related.name AS related_company,
                       related.bse_code AS related_bse_code,
                       r.txn_type AS txn_type,
                       r.amount AS amount, r.year AS year
                ORDER BY r.year DESC
                """,
                bse_code=bse_code,
            )
            return [dict(record) for record in result]

    def get_neighbors(
        self,
        bse_code: str,
        depth: int = 2,
        entity_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Return nodes and edges for a D3 force graph up to `depth` hops.
        """
        type_filter = "|".join(entity_types) if entity_types else "Company|Person|AuditorFirm"
        with self._driver.session() as session:
            result = session.run(
                f"""
                MATCH path = (c:Company {{bse_code: $bse_code}})-[*1..{depth}]-(n)
                WHERE any(label IN labels(n) WHERE label IN $types)
                WITH nodes(path) AS ns, relationships(path) AS rs
                UNWIND ns AS node
                WITH collect(DISTINCT {{
                    id: toString(id(node)),
                    label: labels(node)[0],
                    name: coalesce(node.name, node.bse_code, 'Unknown')
                }}) AS nodes_list, rs
                UNWIND rs AS rel
                WITH nodes_list, collect(DISTINCT {{
                    source: toString(id(startNode(rel))),
                    target: toString(id(endNode(rel))),
                    type: type(rel)
                }}) AS edges_list
                RETURN nodes_list AS nodes, edges_list AS edges
                """,
                bse_code=bse_code,
                types=entity_types or ["Company", "Person", "AuditorFirm"],
            )
            record = result.single()
            if not record:
                return {"nodes": [], "edges": []}
            return {"nodes": record["nodes"], "edges": record["edges"]}


# Singleton
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    global _neo4j_client
    if _neo4j_client is None:
        s = get_settings()
        _neo4j_client = Neo4jClient(s.NEO4J_URI, s.NEO4J_USER, s.NEO4J_PASSWORD)
    return _neo4j_client