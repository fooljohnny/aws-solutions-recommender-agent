"""Normalization and synonyms for industries, business types, and tags.

This is a pragmatic dictionary-based normalizer:
- keeps a canonical English token where possible
- supports common Chinese synonyms
"""

from __future__ import annotations

from typing import Dict, Iterable, List


_CANONICAL: Dict[str, str] = {
    # industries
    "金融": "finance",
    "银行": "finance",
    "保险": "finance",
    "finance": "finance",
    "banking": "finance",
    "insurtech": "finance",
    "零售": "retail",
    "电商": "retail",
    "零售电商": "retail",
    "retail": "retail",
    "ecommerce": "retail",
    "manufacturing": "manufacturing",
    "制造": "manufacturing",
    "工业": "manufacturing",
    "医疗": "healthcare",
    "医药": "healthcare",
    "healthcare": "healthcare",
    "教育": "education",
    "education": "education",
    "政府": "public_sector",
    "政务": "public_sector",
    "public sector": "public_sector",
    "public_sector": "public_sector",
    # business types
    "支付": "payments",
    "收单": "payments",
    "payments": "payments",
    "web": "web",
    "web应用": "web",
    "api": "api",
    "数据分析": "analytics",
    "analytics": "analytics",
    "iot": "iot",
    "物联网": "iot",
}


def normalize_token(s: str) -> str:
    t = (s or "").strip().lower()
    if not t:
        return ""
    # keep original Chinese as key too
    if s in _CANONICAL:
        return _CANONICAL[s]
    if t in _CANONICAL:
        return _CANONICAL[t]
    # normalize separators/spaces
    t2 = t.replace("-", " ").replace("_", " ").strip()
    if t2 in _CANONICAL:
        return _CANONICAL[t2]
    return t


def normalize_list(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for v in values or []:
        if not isinstance(v, str):
            continue
        n = normalize_token(v)
        if not n:
            continue
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out

