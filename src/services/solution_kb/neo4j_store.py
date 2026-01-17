"""Neo4j-backed knowledge graph store for solution templates."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from .models import ParameterSpec, TemplateExtract, TemplateKind, TemplateMetadata, TemplateSource


class Neo4jUnavailable(RuntimeError):
    """Raised when Neo4j store cannot connect or operate."""


class Neo4jSolutionKBStore:
    """Stores TemplateExtract into Neo4j as a property graph and supports retrieval."""

    def __init__(
        self,
        *,
        uri: str,
        user: str,
        password: str,
        database: Optional[str] = None,
    ):
        from neo4j import GraphDatabase  # type: ignore

        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    @classmethod
    def from_env(cls) -> "Neo4jSolutionKBStore":
        uri = (os.getenv("NEO4J_URI") or "").strip()
        user = (os.getenv("NEO4J_USER") or "").strip() or "neo4j"
        password = (os.getenv("NEO4J_PASSWORD") or "").strip()
        database = (os.getenv("NEO4J_DATABASE") or "").strip() or None
        if not uri or not password:
            raise Neo4jUnavailable("NEO4J_URI and NEO4J_PASSWORD must be set for Neo4j backend.")
        return cls(uri=uri, user=user, password=password, database=database)

    def close(self) -> None:
        try:
            self._driver.close()
        except Exception:
            pass

    def ensure_schema(self) -> None:
        """Create uniqueness constraints / indexes (idempotent)."""
        statements = [
            "CREATE CONSTRAINT template_id IF NOT EXISTS FOR (t:Template) REQUIRE t.template_id IS UNIQUE",
            "CREATE CONSTRAINT resource_node_id IF NOT EXISTS FOR (r:Resource) REQUIRE r.node_id IS UNIQUE",
            "CREATE CONSTRAINT parameter_node_id IF NOT EXISTS FOR (p:Parameter) REQUIRE p.node_id IS UNIQUE",
            "CREATE CONSTRAINT output_node_id IF NOT EXISTS FOR (o:Output) REQUIRE o.node_id IS UNIQUE",
            "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (x:Tag) REQUIRE x.name IS UNIQUE",
            "CREATE CONSTRAINT industry_name IF NOT EXISTS FOR (x:Industry) REQUIRE x.name IS UNIQUE",
            "CREATE CONSTRAINT business_type_name IF NOT EXISTS FOR (x:BusinessType) REQUIRE x.name IS UNIQUE",
        ]
        with self._driver.session(database=self._database) as session:
            for cypher in statements:
                session.run(cypher)

    def upsert_many(self, extracts: Iterable[TemplateExtract]) -> None:
        extracts_list = list(extracts)
        if not extracts_list:
            return
        with self._driver.session(database=self._database) as session:
            self.ensure_schema()
            for ex in extracts_list:
                session.execute_write(self._upsert_one_tx, ex.model_dump())

    def search(
        self,
        *,
        keywords: Optional[List[str]] = None,
        resource_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[TemplateExtract]:
        kws = [k.strip().lower() for k in (keywords or []) if k and k.strip()]
        rts = [r.strip() for r in (resource_types or []) if r and r.strip()]

        cypher = """
        MATCH (t:Template)
        WHERE
          ($kws = [] OR any(k IN $kws WHERE t.search_text CONTAINS k))
          AND
          ($rts = [] OR any(rt IN $rts WHERE rt IN t.resource_types))
        WITH t,
          reduce(score = 0.0, k IN $kws |
            score + CASE WHEN t.search_text CONTAINS k THEN 1.0 ELSE 0.0 END
          ) AS score
        OPTIONAL MATCH (t)-[:CONTAINS]->(p:Parameter)
        WITH t, score, collect(DISTINCT p.name) AS param_names
        RETURN
          t.template_id AS template_id,
          t.kind AS kind,
          t.source AS source,
          t.name AS name,
          t.description AS description,
          t.repository AS repository,
          t.path AS path,
          t.tags AS tags,
          t.industries AS industries,
          t.business_types AS business_types,
          t.resource_types AS resource_types,
          t.embedding AS embedding,
          t.embedding_model AS embedding_model,
          param_names AS param_names,
          score AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        rows: List[Dict[str, Any]] = []
        with self._driver.session(database=self._database) as session:
            res = session.run(cypher, kws=kws, rts=rts, limit=limit)
            rows = [dict(r) for r in res]

        out: List[TemplateExtract] = []
        for r in rows:
            meta = TemplateMetadata(
                template_id=UUID(r["template_id"]),
                kind=TemplateKind(r.get("kind") or TemplateKind.UNKNOWN.value),
                source=TemplateSource(r.get("source") or TemplateSource.LOCAL.value),
                name=r.get("name") or "",
                description=r.get("description") or "",
                repository=r.get("repository"),
                path=r.get("path"),
                tags=list(r.get("tags") or []),
                industries=list(r.get("industries") or []),
                business_types=list(r.get("business_types") or []),
                embedding=r.get("embedding"),
                embedding_model=r.get("embedding_model"),
            )
            params = [ParameterSpec(name=p) for p in (r.get("param_names") or []) if isinstance(p, str)]
            resource_types_list = list(r.get("resource_types") or [])
            out.append(
                TemplateExtract(
                    meta=meta,
                    parameters=params,
                    resources=[],
                    outputs=[],
                    resource_types=resource_types_list,
                )
            )
        return out

    def get(self, template_id: UUID) -> Optional[TemplateExtract]:
        """Fetch a template by id (metadata-only)."""
        tid = str(template_id)
        cypher = """
        MATCH (t:Template {template_id: $id})
        OPTIONAL MATCH (t)-[:CONTAINS]->(p:Parameter)
        WITH t, collect(DISTINCT p.name) AS param_names
        RETURN
          t.template_id AS template_id,
          t.kind AS kind,
          t.source AS source,
          t.name AS name,
          t.description AS description,
          t.template_body AS template_body,
          t.repository AS repository,
          t.path AS path,
          t.tags AS tags,
          t.industries AS industries,
          t.business_types AS business_types,
          t.resource_types AS resource_types,
          t.embedding AS embedding,
          t.embedding_model AS embedding_model,
          param_names AS param_names
        """
        with self._driver.session(database=self._database) as session:
            row = session.run(cypher, id=tid).single()
            if not row:
                return None
            r = dict(row)
            meta = TemplateMetadata(
                template_id=UUID(r["template_id"]),
                kind=TemplateKind(r.get("kind") or TemplateKind.UNKNOWN.value),
                source=TemplateSource(r.get("source") or TemplateSource.LOCAL.value),
                name=r.get("name") or "",
                description=r.get("description") or "",
                template_body=r.get("template_body"),
                repository=r.get("repository"),
                path=r.get("path"),
                tags=list(r.get("tags") or []),
                industries=list(r.get("industries") or []),
                business_types=list(r.get("business_types") or []),
                embedding=r.get("embedding"),
                embedding_model=r.get("embedding_model"),
            )
            params = [ParameterSpec(name=p) for p in (r.get("param_names") or []) if isinstance(p, str)]
            return TemplateExtract(
                meta=meta,
                parameters=params,
                resources=[],
                outputs=[],
                resource_types=list(r.get("resource_types") or []),
            )

    def update_template_metadata(
        self,
        template_id: UUID,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        business_types: Optional[List[str]] = None,
    ) -> bool:
        """Patch metadata on an existing Template node (and refresh tag relations)."""
        tid = str(template_id)
        with self._driver.session(database=self._database) as session:
            # Ensure template exists
            exists = session.run("MATCH (t:Template {template_id: $id}) RETURN t.template_id AS id", id=tid).single()
            if not exists:
                return False

            # Update scalar fields
            sets = []
            params: Dict[str, Any] = {"id": tid}
            if name is not None:
                sets.append("t.name = $name")
                params["name"] = name
            if description is not None:
                sets.append("t.description = $description")
                params["description"] = description
            if tags is not None:
                sets.append("t.tags = $tags")
                from .synonyms import normalize_list
                params["tags"] = normalize_list([t for t in tags if isinstance(t, str)])
            if industries is not None:
                sets.append("t.industries = $industries")
                from .synonyms import normalize_list
                params["industries"] = normalize_list([t for t in industries if isinstance(t, str)])
            if business_types is not None:
                sets.append("t.business_types = $business_types")
                from .synonyms import normalize_list
                params["business_types"] = normalize_list([t for t in business_types if isinstance(t, str)])

            if sets:
                session.run(f"MATCH (t:Template {{template_id: $id}}) SET {', '.join(sets)}", **params)

            # Refresh relationships if lists provided (idempotent rebuild)
            if tags is not None:
                session.run(
                    """
                    MATCH (t:Template {template_id: $id})-[r:HAS_TAG]->(:Tag)
                    DELETE r
                    """,
                    id=tid,
                )
                for v in tags:
                    if isinstance(v, str) and v.strip():
                        session.run(
                            """
                            MATCH (t:Template {template_id: $id})
                            MERGE (x:Tag {name: $name})
                            MERGE (t)-[:HAS_TAG]->(x)
                            """,
                            id=tid,
                            name=v.strip(),
                        )

            if industries is not None:
                session.run(
                    """
                    MATCH (t:Template {template_id: $id})-[r:HAS_INDUSTRY]->(:Industry)
                    DELETE r
                    """,
                    id=tid,
                )
                for v in industries:
                    if isinstance(v, str) and v.strip():
                        session.run(
                            """
                            MATCH (t:Template {template_id: $id})
                            MERGE (x:Industry {name: $name})
                            MERGE (t)-[:HAS_INDUSTRY]->(x)
                            """,
                            id=tid,
                            name=v.strip(),
                        )

            if business_types is not None:
                session.run(
                    """
                    MATCH (t:Template {template_id: $id})-[r:HAS_BUSINESS_TYPE]->(:BusinessType)
                    DELETE r
                    """,
                    id=tid,
                )
                for v in business_types:
                    if isinstance(v, str) and v.strip():
                        session.run(
                            """
                            MATCH (t:Template {template_id: $id})
                            MERGE (x:BusinessType {name: $name})
                            MERGE (t)-[:HAS_BUSINESS_TYPE]->(x)
                            """,
                            id=tid,
                            name=v.strip(),
                        )

        return True

    def suggest_connected_resource_types(
        self,
        *,
        resource_type: str,
        relation: str = "both",
        direction: str = "out",
        industries: Optional[List[str]] = None,
        business_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Tuple[str, int]]:
        """Suggest which resource types are most often connected to a given resource type.

        Uses the graph edges between Resource nodes:
        - :DEPENDS_ON
        - :REFERENCES

        Args:
            resource_type: e.g. "AWS::Lambda::Function"
            relation: "depends_on" | "references" | "both"
            direction: "out" (A -> B) | "in" (X -> A) | "both"
            industries: optional filter on Template.industries
            business_types: optional filter on Template.business_types
            limit: max target types to return
        """
        rt = (resource_type or "").strip()
        if not rt:
            return []

        rel = (relation or "both").strip().lower()
        if rel not in {"depends_on", "references", "both"}:
            rel = "both"

        dirn = (direction or "out").strip().lower()
        if dirn not in {"out", "in", "both"}:
            dirn = "out"

        ind = [x.strip() for x in (industries or []) if isinstance(x, str) and x.strip()]
        bt = [x.strip() for x in (business_types or []) if isinstance(x, str) and x.strip()]

        if rel == "depends_on":
            rels = ["DEPENDS_ON"]
        elif rel == "references":
            rels = ["REFERENCES"]
        else:
            rels = ["DEPENDS_ON", "REFERENCES"]

        if dirn == "out":
            match_rel = "MATCH (a)-[r]->(b:Resource)"
            where_a = "a.type = $rt"
            where_b = "TRUE"
            return_field = "b.type AS target_type"
        elif dirn == "in":
            match_rel = "MATCH (a:Resource)-[r]->(b)"
            where_a = "TRUE"
            where_b = "b.type = $rt"
            return_field = "a.type AS target_type"
        else:
            # both: treat edges as undirected for type-to-type co-occurrence via relations
            match_rel = "MATCH (a)-[r]-(b:Resource)"
            where_a = "a.type = $rt"
            where_b = "TRUE"
            return_field = "b.type AS target_type"

        cypher = f"""
        MATCH (t:Template)-[:CONTAINS]->(a:Resource)
        WHERE {where_a}
          AND ($ind = [] OR any(x IN $ind WHERE x IN t.industries))
          AND ($bt = [] OR any(x IN $bt WHERE x IN t.business_types))
        {match_rel}
        WHERE type(r) IN $rels AND {where_b}
        RETURN {return_field}, count(*) AS cnt
        ORDER BY cnt DESC
        LIMIT $limit
        """
        with self._driver.session(database=self._database) as session:
            res = session.run(cypher, rt=rt, rels=rels, ind=ind, bt=bt, limit=limit)
            return [(row["target_type"], int(row["cnt"])) for row in res if row.get("target_type")]

    @staticmethod
    def _upsert_one_tx(tx, ex: Dict[str, Any]) -> None:
        meta = ex["meta"]
        template_id = str(meta["template_id"])

        tags = meta.get("tags") or []
        industries = meta.get("industries") or []
        business_types = meta.get("business_types") or []
        resource_types = ex.get("resource_types") or []

        search_text = " ".join(
            [
                str(meta.get("name") or ""),
                str(meta.get("description") or ""),
                " ".join([str(x) for x in tags]),
                " ".join([str(x) for x in industries]),
                " ".join([str(x) for x in business_types]),
                " ".join([str(x) for x in resource_types]),
            ]
        ).lower()

        tx.run(
            """
            MERGE (t:Template {template_id: $template_id})
            SET
              t.kind = $kind,
              t.source = $source,
              t.name = $name,
              t.description = $description,
              t.template_body = $template_body,
              t.repository = $repository,
              t.path = $path,
              t.collected_at = $collected_at,
              t.tags = $tags,
              t.industries = $industries,
              t.business_types = $business_types,
              t.resource_types = $resource_types,
              t.embedding = $embedding,
              t.embedding_model = $embedding_model,
              t.search_text = $search_text
            """,
            template_id=template_id,
            kind=str(meta.get("kind") or "unknown"),
            source=str(meta.get("source") or "local"),
            name=str(meta.get("name") or ""),
            description=str(meta.get("description") or ""),
            template_body=meta.get("template_body"),
            repository=meta.get("repository"),
            path=meta.get("path"),
            collected_at=str(meta.get("collected_at") or ""),
            tags=tags,
            industries=industries,
            business_types=business_types,
            resource_types=resource_types,
            embedding=meta.get("embedding"),
            embedding_model=meta.get("embedding_model"),
            search_text=search_text,
        )

        # Tag / industry / business type nodes
        for label, rel, values in [
            ("Tag", "HAS_TAG", tags),
            ("Industry", "HAS_INDUSTRY", industries),
            ("BusinessType", "HAS_BUSINESS_TYPE", business_types),
        ]:
            for v in values:
                if not isinstance(v, str) or not v.strip():
                    continue
                tx.run(
                    f"""
                    MATCH (t:Template {{template_id: $template_id}})
                    MERGE (x:{label} {{name: $name}})
                    MERGE (t)-[:{rel}]->(x)
                    """,
                    template_id=template_id,
                    name=v.strip(),
                )

        # Parameters
        for p in ex.get("parameters") or []:
            if not isinstance(p, dict) or not p.get("name"):
                continue
            node_id = f"{template_id}:param:{p['name']}"
            tx.run(
                """
                MATCH (t:Template {template_id: $template_id})
                MERGE (p:Parameter {node_id: $node_id})
                SET
                  p.template_id = $template_id,
                  p.name = $name,
                  p.type = $type,
                  p.default = $default,
                  p.description = $description
                MERGE (t)-[:CONTAINS]->(p)
                """,
                template_id=template_id,
                node_id=node_id,
                name=p.get("name"),
                type=p.get("type"),
                default=p.get("default"),
                description=p.get("description"),
            )

        # Resources
        for r in ex.get("resources") or []:
            if not isinstance(r, dict) or not r.get("logical_id") or not r.get("type"):
                continue
            node_id = f"{template_id}:res:{r['logical_id']}"
            props_json = json.dumps(r.get("properties") or {}, ensure_ascii=False)
            tx.run(
                """
                MATCH (t:Template {template_id: $template_id})
                MERGE (r:Resource {node_id: $node_id})
                SET
                  r.template_id = $template_id,
                  r.logical_id = $logical_id,
                  r.type = $type,
                  r.properties_json = $properties_json
                MERGE (t)-[:CONTAINS]->(r)
                """,
                template_id=template_id,
                node_id=node_id,
                logical_id=r.get("logical_id"),
                type=r.get("type"),
                properties_json=props_json,
            )

        # Outputs (minimal)
        for o in ex.get("outputs") or []:
            if not isinstance(o, dict) or not o.get("name"):
                continue
            node_id = f"{template_id}:out:{o['name']}"
            value_json = json.dumps(o.get("value"), ensure_ascii=False)
            export_json = json.dumps(o.get("export_name"), ensure_ascii=False)
            tx.run(
                """
                MATCH (t:Template {template_id: $template_id})
                MERGE (o:Output {node_id: $node_id})
                SET
                  o.template_id = $template_id,
                  o.name = $name,
                  o.description = $description,
                  o.value_json = $value_json,
                  o.export_name_json = $export_name_json
                MERGE (t)-[:CONTAINS]->(o)
                """,
                template_id=template_id,
                node_id=node_id,
                name=o.get("name"),
                description=o.get("description"),
                value_json=value_json,
                export_name_json=export_json,
            )

        # Relationships between resources (DEPENDS_ON / REFERENCES)
        for r in ex.get("resources") or []:
            if not isinstance(r, dict) or not r.get("logical_id"):
                continue
            src_node_id = f"{template_id}:res:{r['logical_id']}"

            for dep in r.get("depends_on") or []:
                if not isinstance(dep, str) or not dep.strip():
                    continue
                dst_node_id = f"{template_id}:res:{dep.strip()}"
                tx.run(
                    """
                    MATCH (a:Resource {node_id: $a}), (b:Resource {node_id: $b})
                    MERGE (a)-[:DEPENDS_ON]->(b)
                    """,
                    a=src_node_id,
                    b=dst_node_id,
                )

            for ref in r.get("references") or []:
                if not isinstance(ref, str) or not ref.strip():
                    continue
                # Prefer linking to Resource; fallback to Parameter if exists.
                dst_res = f"{template_id}:res:{ref.strip()}"
                dst_param = f"{template_id}:param:{ref.strip()}"
                tx.run(
                    """
                    MATCH (a:Resource {node_id: $a})
                    OPTIONAL MATCH (b:Resource {node_id: $dst_res})
                    OPTIONAL MATCH (c:Parameter {node_id: $dst_param})
                    WITH a, coalesce(b, c) AS target
                    WHERE target IS NOT NULL
                    MERGE (a)-[:REFERENCES]->(target)
                    """,
                    a=src_node_id,
                    dst_res=dst_res,
                    dst_param=dst_param,
                )

