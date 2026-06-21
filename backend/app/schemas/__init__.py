"""Pydantic response schemas documenting the API contract.

Routes currently return plain dicts for flexibility; these models document the
intended shapes and can be wired in as `response_model` if stricter validation is
desired.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class NodeData(BaseModel):
    id: str
    label: str
    title: Optional[str] = None
    lifecycle_status: Optional[str] = None
    rank: Optional[str] = None
    url_html: Optional[str] = None
    is_live: Optional[bool] = None
    metrics: Dict[str, Any] = {}


class GraphNode(BaseModel):
    data: NodeData


class EdgeData(BaseModel):
    id: str
    source: str
    target: str
    relation_type: str
    relation_label_raw: Optional[str] = None
    relation_detail_raw: Optional[str] = None


class GraphEdge(BaseModel):
    data: EdgeData


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class Summary(BaseModel):
    total_norms: int
    total_relations: int
    relation_counts_by_type: Dict[str, int]
    lifecycle_counts: Dict[str, int]
    default_scope: str
    scope_label: str
    last_ingestion_at: Optional[str] = None
