"""
run_inference.py

Unified inference script for CivilTime-Benchmark.
Supports:
- Zero-shot
- Few-shot (ICL)
- Refinement (conceptually similar to zero/few shot but usually involves a second pass - here we implement standard generation which can be used for any phase)
"""

import os
import json
import time
import argparse
import torch
import random
from pathlib import Path
from typing import List, Dict, Any

from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def build_prompt(
    item: Dict[str, Any],
    method: str,
    shots: int = 0,
    exemplars: Dict[str, List] = None
) -> str:
    """Construct prompt based on method and item."""
    # Simplified prompt construction
    sys_msg = (
        "You are a precise time and calendar engine. Follow ISO-8601 strictly. "
        "Return ONLY one JSON object. If ambiguous, output "
        '{"abstain": true, "reason": "..."}. '
        "Do not output prose."
    )
    
    user_text = item.get("input_text") or item.get("task_text") or item.get("instruction") or ""
    
    if method == "icl" and shots > 0 and exemplars:
        # Inject exemplars
        q_type = item.get("type", "UNKNOWN")
        ex_list = exemplars.get(q_type, [])[:shots]
        
        prompt = sys_msg + "\n\n"
        for ex in ex_list:
            # Assume exemplars have 'input' and 'output'
            p_in = ex.get("input", "")
            p_out = ex.get("output", "")
            prompt += f"User: {p_in}\nAssistant: {p_out}\n\n"
        
        prompt += f"User: {user_text}\nAssistant:"
        return prompt

    if method == "refinement":
        # Maybe refinement uses a different system prompt or prompt structure
        # For now treat as Zero-shot with specific instructions if needed
        pass

    # Zero-shot default
    return f"{sys_msg}\n\nUser: {user_text}\nAssistant:"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="HF model ID or path")
    parser.add_argument("--data", required=True, help="Input JSONL")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--method", choices=["zeroshot", "icl"], default="zeroshot")
    parser.add_argument("--shots", type=int, default=0)
    parser.add_argument("--exemplars_file", help="Path to JSONL with exemplars for ICL")
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--token", help="HF Token", default=None)
    parser.add_argument("--max_items", type=int, help="Debug limit", default=None)
    args = parser.parse_args()

    # Login if needed
    if args.token:
        from huggingface_hub import login
        login(args.token)

    # Load data
    data = load_jsonl(args.data)
    if args.max_items:
        data = data[:args.max_items]

    # Load exemplars if ICL
    exemplars_map = {}
    if args.method == "icl":
        if not args.exemplars_file:
            print("Warning: ICL requested but no exemplars_file provided.")
        else:
            raw_ex = load_jsonl(args.exemplars_file)
            # Group by type
            for ex in raw_ex:
                t = ex.get("type", "UNKNOWN")
                if t not in exemplars_map: exemplars_map[t] = []
                exemplars_map[t].append(ex)

    # Load Model
    print(f"Loading model: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model, padding_side="left")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map="auto",
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )
    model.eval()

    # Generate
    results = []
    batch = []
    
    print(f"Starting inference on {len(data)} items...")
    
    for i, item in enumerate(data):
        prompt = build_prompt(item, args.method, args.shots, exemplars_map)
        batch.append((item, prompt))
        
        if len(batch) >= args.batch_size or i == len(data) - 1:
            prompts = [b[1] for b in batch]
            inputs = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True, max_length=2048).to(model.device)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs, 
                    max_new_tokens=256, 
                    do_sample=False, 
                    temperature=0.0
                )
            
            # Decode
            for j, (itm, prmt) in enumerate(batch):
                input_len = inputs.input_ids[j].shape[0]
                # Slice logic can be tricky with padding, simple decode for now
                generated = tokenizer.decode(outputs[j], skip_special_tokens=True)
                # Strip prompt roughly
                # Ideally use more robust slicing like in qwen script
                # Fallback: just save full text
                
                # Try to strip prompt if it's a prefix
                # A robust way is usually `generated[len(prmt):]` but tokenization differs
                # Let's just save the raw text for the fixer script
                
                results.append({
                    "id": itm.get("id"),
                    "type": itm.get("type"),
                    "raw_response": generated
                })
            
            batch = []
            
            if len(results) % 10 == 0:
                print(f"Processed {len(results)}...")

    # Save
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
            
    print(f"Done. Saved to {args.output}")

if __name__ == "__main__":
    main()
