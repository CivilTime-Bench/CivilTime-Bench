"""
evaluate.py

Standardized evaluation script for CivilTime-Benchmark.
Calculates Exact Match (EM) and Temporal Error.
"""

import argparse
import json
import re
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

ISO_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+\-]\d{2}:\d{2})$")

ALL_TYPES = [
    "BUSINESS_DAY", "CONSTRAINTS", "DATE_LINE", "DST_AMBIG", "DST_REPEAT",
    "DST_SKIP", "INTERVAL", "ISO_WEEK", "OFFSET", "RELATIVE_DAY", "WEEKSTART"
]

def is_iso_ok(text: str) -> bool:
    s = str(text).strip()
    if s == "ABSTAIN": return True
    if "||" in s:
        parts = [p.strip() for p in s.split("||")]
        return len(parts) == 2 and all(ISO_PATTERN.match(p) for p in parts)
    return ISO_PATTERN.match(s) is not None

def _parse_single(text: str) -> int:
    s = text.strip()
    if s.endswith("Z"): s = s[:-1] + "+00:00"
    return int(datetime.fromisoformat(s).timestamp())

def parse_unix(text: str):
    if not is_iso_ok(text): raise ValueError("Not ISO")
    s = text.strip()
    if s == "ABSTAIN": raise ValueError("ABSTAIN")
    if "||" in s:
        return [_parse_single(p) for p in s.split("||")]
    return _parse_single(s)

def temporal_error(gold: str, pred: str, is_interval: bool = False) -> Optional[int]:
    gold, pred = gold.strip(), pred.strip()
    if gold == "ABSTAIN" or pred == "ABSTAIN": return None
    try:
        g = parse_unix(gold)
        p = parse_unix(pred)
    except ValueError:
        return None

    # List vs List
    if isinstance(g, list) and isinstance(p, list):
        if len(g) != 2 or len(p) != 2: return None
        if is_interval:
            return max(abs(p[0]-g[0]), abs(p[1]-g[1]))
        return min(abs(pa-ga) for pa in p for ga in g)
    
    # List vs Scalar
    if isinstance(g, list) and isinstance(p, int):
        return min(abs(p-g[0]), abs(p-g[1]))
        
    # Scalar vs Scalar
    if isinstance(g, int) and isinstance(p, int):
        return abs(p-g)
        
    return None

def evaluate(preds_path: Path, gold_path: Path, output_dir: Path):
    print(f"Loading predictions: {preds_path}")
    preds = {}
    with open(preds_path) as f:
        for line in f:
            obj = json.loads(line)
            preds[str(obj["id"])] = str(obj.get("pred", "")).strip()

    print(f"Loading gold: {gold_path}")
    rows = []
    with open(gold_path) as f:
        for line in f:
            obj = json.loads(line)
            rows.append(obj)

    results = []
    for row in rows:
        rid = str(row["id"])
        gold = str(row["gold"]).strip()
        row_type = row.get("type", "UNKNOWN")
        
        pred = preds.get(rid, "")
        
        # Logic: if gold has ||, match either
        match = False
        if "||" in gold and "||" not in pred:
            parts = [p.strip() for p in gold.split("||")]
            if pred in parts:
                match = True
        else:
            match = (pred == gold)
            
        em = 1 if match else 0
        
        # Temporal error
        is_int = (row_type == "INTERVAL")
        # For TE, we align pred to the 'matched' gold part if ambiguous
        # Simplified: just compute TE against full gold string logic
        te = temporal_error(gold, pred, is_interval=is_int)
        
        results.append({
            "id": rid,
            "type": row_type,
            "em": em,
            "te": te,
            "format_ok": is_iso_ok(pred)
        })

    df = pd.DataFrame(results)
    
    # Metrics
    summary = {
        "n": len(df),
        "em": df["em"].mean(),
        "format_ok": df["format_ok"].mean(),
        "median_te": df["te"].median()
    }
    
    by_type = df.groupby("type")[["em", "format_ok", "te"]].mean()
    # te mean is not median, but acceptable for quick view. better to aggregate manual
    by_type["median_te"] = df.groupby("type")["te"].median()

    print("\n=== RESULTS ===")
    print(json.dumps(summary, indent=2))
    print("\n=== BY TYPE ===")
    print(by_type)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    by_type_path = output_dir / "by_type.csv"
    
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    by_type.to_csv(by_type_path)
    print(f"\nSaved results to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preds", required=True, help="Fixed predictions JSONL")
    parser.add_argument("--gold", required=True, help="Gold dataset JSONL")
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()
    
    evaluate(Path(args.preds), Path(args.gold), Path(args.output_dir))
