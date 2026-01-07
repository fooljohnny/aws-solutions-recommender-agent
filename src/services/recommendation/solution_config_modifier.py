"""Natural-language modifications to solution configuration (region/AZ/spec/quantity/params)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


_REGION_RE = re.compile(r"\b([a-z]{2}-[a-z]+-\d)\b", re.IGNORECASE)
_AZ_RE = re.compile(r"\b([a-z]{2}-[a-z]+-\d[a-z])\b", re.IGNORECASE)
_EC2_TYPE_RE = re.compile(r"\b(t\d\.[a-z0-9]+|m\d\.[a-z0-9]+|c\d\.[a-z0-9]+|r\d\.[a-z0-9]+)\b", re.IGNORECASE)
_RDS_CLASS_RE = re.compile(r"\b(db\.[a-z0-9]+\.[a-z0-9]+)\b", re.IGNORECASE)


_ZH_NUM = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def _parse_intish(s: str) -> Optional[int]:
    s = (s or "").strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    if s in _ZH_NUM:
        return _ZH_NUM[s]
    return None


@dataclass(frozen=True)
class Modification:
    region: Optional[str] = None
    azs: Optional[List[str]] = None
    ec2_instance_type: Optional[str] = None
    rds_instance_class: Optional[str] = None
    quantities: Optional[Dict[str, int]] = None  # by service name
    params: Optional[Dict[str, object]] = None  # generic key=value params applied to all services


class SolutionConfigModifier:
    """Parse user text into config modifications and apply to fulfillment dict."""

    def parse(self, text: str) -> Modification:
        msg = (text or "").strip()
        region = None
        azs: List[str] = []

        m = _REGION_RE.search(msg)
        if m:
            region = m.group(1).lower()
        for m2 in _AZ_RE.finditer(msg):
            azs.append(m2.group(1).lower())
        azs = sorted(set(azs))

        ec2_type = None
        m3 = _EC2_TYPE_RE.search(msg)
        if m3:
            ec2_type = m3.group(1).lower()

        rds_class = None
        m4 = _RDS_CLASS_RE.search(msg)
        if m4:
            rds_class = m4.group(1).lower()

        quantities: Dict[str, int] = {}
        # Very small patterns: "EC2 3台" / "RDS 两个" / "2台EC2"
        for svc in ("EC2", "RDS"):
            pat1 = re.compile(rf"{svc}\s*([0-9一二两三四五六七八九十]+)\s*(台|个)?", re.IGNORECASE)
            pat2 = re.compile(rf"([0-9一二两三四五六七八九十]+)\s*(台|个)?\s*{svc}", re.IGNORECASE)
            for pat in (pat1, pat2):
                mm = pat.search(msg)
                if not mm:
                    continue
                n = _parse_intish(mm.group(1))
                if n is not None and n > 0:
                    quantities[svc] = n
                    break

        params: Dict[str, object] = {}
        # Parse key=value tokens (e.g., multi_az=false, storage_gb=200)
        for km in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^\s,，;；]+)\b", msg):
            k = km.group(1)
            vraw = km.group(2)
            v: object = vraw
            if vraw.lower() in {"true", "false"}:
                v = vraw.lower() == "true"
            elif vraw.isdigit():
                v = int(vraw)
            params[k] = v

        return Modification(
            region=region,
            azs=azs or None,
            ec2_instance_type=ec2_type,
            rds_instance_class=rds_class,
            quantities=quantities or None,
            params=params or None,
        )

    def apply_to_fulfillment(
        self,
        fulfillment: Dict[str, Dict[str, object]],
        mod: Modification,
    ) -> Dict[str, Dict[str, object]]:
        """Apply modifications to a fulfillment dict (pure function)."""
        out: Dict[str, Dict[str, object]] = {k: dict(v) for k, v in (fulfillment or {}).items()}

        if mod.quantities:
            for svc, qty in mod.quantities.items():
                if svc in out:
                    out[svc]["quantity"] = int(qty)

        if mod.ec2_instance_type and "EC2" in out:
            spec = dict(out["EC2"].get("spec") or {})
            spec["instance_type"] = mod.ec2_instance_type
            out["EC2"]["spec"] = spec

        if mod.rds_instance_class and "RDS" in out:
            spec = dict(out["RDS"].get("spec") or {})
            spec["instance_class"] = mod.rds_instance_class
            out["RDS"]["spec"] = spec

        if mod.azs:
            for svc in out:
                out[svc]["chosen_azs"] = list(mod.azs)

        if mod.params:
            for svc in out:
                defaults = dict(out[svc].get("defaults") or {})
                defaults.update(mod.params)
                out[svc]["defaults"] = defaults

        return out

