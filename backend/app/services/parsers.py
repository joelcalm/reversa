"""Parse raw BOE JSON payloads into normalized norm records and directed edges.

These functions are pure and defensive: they tolerate missing keys and varied shapes
and never raise on partial data. Edge direction is the most safety-critical concern,
so it is implemented explicitly and covered by tests.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, List, Optional

from app.core.config import boe_html_url
from app.services.lifecycle import compute_lifecycle
from app.services.relation_normalizer import normalize_relation

# api_direction markers
DIR_ANTERIOR = "anteriores"
DIR_POSTERIOR = "posteriores"


@dataclass
class ParsedNorm:
    id: str
    title: str
    official_number: Optional[str] = None
    rank_code: Optional[str] = None
    rank: Optional[str] = None
    scope_code: Optional[str] = None
    scope: Optional[str] = None
    department_code: Optional[str] = None
    department: Optional[str] = None
    disposition_date: Optional[str] = None
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    repeal_date: Optional[str] = None
    annulment_date: Optional[str] = None
    exhausted_validity: Optional[str] = None
    estatus_derogacion: Optional[str] = None
    estatus_anulacion: Optional[str] = None
    vigencia_agotada: Optional[str] = None
    consolidation_status_code: Optional[str] = None
    consolidation_status: Optional[str] = None
    lifecycle_status: str = "LIVE"
    is_live: bool = True
    is_repealed: bool = False
    url_eli: Optional[str] = None
    url_html: Optional[str] = None
    last_updated: Optional[str] = None
    raw_json: Optional[str] = None


@dataclass
class ParsedRelation:
    source_norm_id: str
    target_norm_id: str
    relation_type: str
    relation_code: Optional[str]
    relation_label_raw: Optional[str]
    relation_detail_raw: Optional[str]
    api_direction: str
    current_norm_id: str


@dataclass
class ParsedSubject:
    code: str
    label: str


@dataclass
class ParsedAnalysis:
    relations: List[ParsedRelation] = field(default_factory=list)
    subjects: List[ParsedSubject] = field(default_factory=list)


def _first(payload: Any) -> Optional[dict]:
    """BOE wraps single objects in a one-element list. Normalize to a dict."""
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict):
        return payload
    return None


def _node_text(obj: Any) -> Optional[str]:
    if isinstance(obj, dict):
        return obj.get("texto")
    return obj if isinstance(obj, str) else None


def _node_code(obj: Any) -> Optional[str]:
    if isinstance(obj, dict):
        return obj.get("codigo")
    return None


def parse_metadata(payload: Any) -> Optional[ParsedNorm]:
    """Parse a metadata payload (or a list item) into a ParsedNorm."""
    meta = _first(payload)
    if not meta:
        return None
    norm_id = meta.get("identificador")
    if not norm_id:
        return None

    estatus_derogacion = meta.get("estatus_derogacion")
    estatus_anulacion = meta.get("estatus_anulacion")
    vigencia_agotada = meta.get("vigencia_agotada")
    life = compute_lifecycle(estatus_derogacion, estatus_anulacion, vigencia_agotada)

    return ParsedNorm(
        id=norm_id,
        title=meta.get("titulo") or norm_id,
        official_number=meta.get("numero_oficial"),
        rank_code=_node_code(meta.get("rango")),
        rank=_node_text(meta.get("rango")),
        scope_code=_node_code(meta.get("ambito")),
        scope=_node_text(meta.get("ambito")),
        department_code=_node_code(meta.get("departamento")),
        department=_node_text(meta.get("departamento")),
        disposition_date=meta.get("fecha_disposicion"),
        publication_date=meta.get("fecha_publicacion"),
        effective_date=meta.get("fecha_vigencia"),
        repeal_date=meta.get("fecha_derogacion"),
        annulment_date=meta.get("fecha_anulacion"),
        exhausted_validity=vigencia_agotada,
        estatus_derogacion=estatus_derogacion,
        estatus_anulacion=estatus_anulacion,
        vigencia_agotada=vigencia_agotada,
        consolidation_status_code=_node_code(meta.get("estado_consolidacion")),
        consolidation_status=_node_text(meta.get("estado_consolidacion")),
        lifecycle_status=life.status,
        is_live=life.is_live,
        is_repealed=life.is_repealed,
        url_eli=meta.get("url_eli"),
        url_html=meta.get("url_html_consolidada") or boe_html_url(norm_id),
        last_updated=meta.get("fecha_actualizacion"),
        raw_json=json.dumps(meta, ensure_ascii=False),
    )


def _iter_reference_items(direction_block: Any, inner_key: str):
    """`anteriores`/`posteriores` are lists of dicts each holding an inner list.

    Shape: [{"anterior": [ {item}, {item} ]}]. Be tolerant of variations where the
    block is already a flat list of items.
    """
    if not direction_block:
        return
    if isinstance(direction_block, dict):
        direction_block = [direction_block]
    for group in direction_block:
        if isinstance(group, dict) and inner_key in group:
            items = group.get(inner_key) or []
        elif isinstance(group, dict) and ("id_norma" in group or "relacion" in group):
            items = [group]
        else:
            items = group if isinstance(group, list) else []
        for item in items:
            if isinstance(item, dict):
                yield item


def parse_analysis(current_norm_id: str, payload: Any) -> ParsedAnalysis:
    """Parse an analisis payload into directed relations + subjects.

    Direction rules:
      - `anteriores` (this norm acts on an earlier norm B): current --TYPE--> B
      - `posteriores` (a later norm C acts on this norm): C --TYPE--> current
    """
    result = ParsedAnalysis()
    block = _first(payload)
    if not block:
        return result

    refs = block.get("referencias") if isinstance(block, dict) else None
    if isinstance(refs, dict):
        for item in _iter_reference_items(refs.get("anteriores"), "anterior"):
            rel = _build_relation(current_norm_id, item, DIR_ANTERIOR)
            if rel:
                result.relations.append(rel)
        for item in _iter_reference_items(refs.get("posteriores"), "posterior"):
            rel = _build_relation(current_norm_id, item, DIR_POSTERIOR)
            if rel:
                result.relations.append(rel)

    materias = block.get("materias") if isinstance(block, dict) else None
    if isinstance(materias, list):
        for m in materias:
            node = m.get("materia") if isinstance(m, dict) else None
            code = _node_code(node)
            label = _node_text(node)
            if code and label:
                result.subjects.append(ParsedSubject(code=code, label=label))

    return result


def _build_relation(
    current_norm_id: str, item: dict, direction: str
) -> Optional[ParsedRelation]:
    other_id = item.get("id_norma")
    if not other_id:
        return None
    relacion = item.get("relacion") or {}
    label_raw = _node_text(relacion)
    code = _node_code(relacion)
    detail = item.get("texto")
    rel_type = normalize_relation(label_raw or "")

    if direction == DIR_ANTERIOR:
        # current norm acts on the earlier norm: current --> other
        source, target = current_norm_id, other_id
    else:
        # a later norm acts on the current norm: other --> current
        source, target = other_id, current_norm_id

    return ParsedRelation(
        source_norm_id=source,
        target_norm_id=target,
        relation_type=rel_type,
        relation_code=code,
        relation_label_raw=label_raw,
        relation_detail_raw=detail,
        api_direction=direction,
        current_norm_id=current_norm_id,
    )
