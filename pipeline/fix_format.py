"""
fix_format.py

Refactored logic to cleanup/normalize raw model predictions into a standardized format.
Extracted from original 'fix_refine_and_zero_shot.py'.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import datetime

# --- Patterns ---
# ISO-8601 datetime with timezone offset
ISO_PATTERN = re.compile(
    r"(?P<full>\d{4}-\d{2}-\d{2}T\d{2}:(?P<min>\d{2})(?::(?P<sec>\d{2}))?)\s*(?P<offset>Z|[+\-]\d{2}:?\d{2}|[+\-]\d{2})\b"
)
ISO_WEEK_PATTERN = re.compile(r"\b(?P<full>\d{4}-W\d{2})\b", re.IGNORECASE)
FINAL_TOKENS = ["final answer", "final:", "answer:", "prediction", "pred:", "result", "output", "iso-8601", "iso8601"]

def normalize_iso(matched_text: str) -> str:
    """Normalize a matched ISO-8601 timestamp to include seconds and a ±HH:MM offset."""
    m = ISO_PATTERN.search(matched_text)
    if not m:
        return matched_text.strip()

    base = m.group("full")
    sec = m.group("sec")
    if not sec:
        base = f"{base}:00"

    offset = m.group("offset").strip()
    if offset == "Z":
        offset_fmt = "+00:00"
    else:
        offset_clean = offset.replace(":", "")
        if len(offset_clean) == 3:   # e.g., ±HH
            offset_clean += "00"
        offset_fmt = f"{offset_clean[:3]}:{offset_clean[3:]}"
    return base + offset_fmt

def _score_candidates(cands: List[Tuple[str, int, int]], text: str) -> List[Tuple[str, float]]:
    """Heuristic scoring to pick the likely 'final' answer."""
    if not cands:
        return []
    low = text.lower()
    tok_positions = []
    for t in FINAL_TOKENS:
        start = 0
        while True:
            i = low.find(t, start)
            if i == -1: break
            tok_positions.append(i)
            start = i + 1
    if not tok_positions:
        tok_positions = [len(text) // 2]

    scored = []
    for s, a, b in cands:
        base = a / max(len(text), 1)
        closest = min(abs(a - tp) for tp in tok_positions)
        prox = 1.0 / (1.0 + closest)
        tz_bonus = 0.05 if not s.endswith("+00:00") else 0.0
        scored.append((s, base + 2.0 * prox + tz_bonus))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

def extract_candidates(text: str) -> Dict[str, List[Tuple[str, int, int]]]:
    """Find all datetime and iso-week candidates."""
    # Datetimes
    dt_matches = [(m.group(0), m.start(), m.end()) for m in ISO_PATTERN.finditer(text)]
    dt_norm = [(normalize_iso(s), a, b) for s, a, b in dt_matches]
    
    seen_dt = set()
    dt_ordered = []
    for s, a, b in dt_norm:
        if s not in seen_dt:
            seen_dt.add(s)
            dt_ordered.append((s, a, b))

    # Weeks
    w_matches = [(m.group(0), m.start(), m.end()) for m in ISO_WEEK_PATTERN.finditer(text)]
    seen_w = set()
    w_ordered = []
    for s, a, b in w_matches:
        ss = s.upper().replace("w", "W")
        if ss not in seen_w:
            seen_w.add(ss)
            w_ordered.append((ss, a, b))
            
    return {"datetimes": dt_ordered, "weeks": w_ordered}

def select_answer(q_type: str, raw_text: str) -> str:
    cands = extract_candidates(raw_text)
    
    if q_type == "ISO_WEEK":
        # Simplified week logic: best week candidate, fallback to datetime derived
        if cands["weeks"]:
            ranked = _score_candidates(cands["weeks"], raw_text)
            return ranked[0][0]
        # Fallback: derive from best datetime
        if cands["datetimes"]:
            best_dt = _score_candidates(cands["datetimes"], raw_text)[0][0]
            try:
                dt = datetime.datetime.fromisoformat(best_dt.replace("Z", "+00:00"))
                y, w, _ = dt.isocalendar()
                return f"{y}-W{w:02d}"
            except:
                pass
        return ""

    # Default: best datetime
    dts = cands["datetimes"]
    if not dts:
        return ""
    ranked = _score_candidates(dts, raw_text)
    return ranked[0][0]

def fix_predictions_file(input_path: Path, output_path: Path):
    """Read raw predictions (JSONL), fix format, write clean JSONL."""
    print(f"Fixing format: {input_path} -> {output_path}")
    
    records = []
    with open(input_path, "r", encoding="utf-8") as fin:
        for line in fin:
            if not line.strip(): continue
            obj = json.loads(line)
            
            # Find raw text
            raw = obj.get("raw_response") or obj.get("raw") or obj.get("prediction") or obj.get("output") or ""
            if isinstance(raw, list): # handle chat history?
                raw = str(raw)
            
            q_type = obj.get("type", "UNKNOWN")
            fixed = select_answer(q_type, str(raw))
            
            records.append({
                "id": obj.get("id"),
                "type": q_type,
                "pred": fixed
            })
            
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fout:
        for r in records:
            fout.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Done. Processed {len(records)} records.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python fix_format.py <input_jsonl> <output_jsonl>")
        sys.exit(1)
    fix_predictions_file(Path(sys.argv[1]), Path(sys.argv[2]))
