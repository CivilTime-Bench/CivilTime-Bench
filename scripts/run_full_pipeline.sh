#!/bin/bash
# run_full_pipeline.sh
# Example end-to-end usage of CivilTime-Benchmark

set -e

# Configuration
MODEL="Qwen/Qwen2.5-7B-Instruct"  # Change to your model
DATA_PATH="../data/10k_eval/eval_10k.jsonl"
OUTPUT_DIR="../results/qwen_7b_zeroshot"
mkdir -p "$OUTPUT_DIR"

RAW_PREDS="$OUTPUT_DIR/raw_preds.jsonl"
FIXED_PREDS="$OUTPUT_DIR/fixed_preds.jsonl"
EVAL_RESULTS="$OUTPUT_DIR/eval_metrics"

echo "[1/3] Running Inference..."
python3 ../pipeline/run_inference.py \
    --model "$MODEL" \
    --data "$DATA_PATH" \
    --output "$RAW_PREDS" \
    --method zeroshot \
    --batch_size 4
    # Add --token <your_token> if needed

echo "[2/3] Fixing Formats..."
python3 ../pipeline/fix_format.py \
    "$RAW_PREDS" \
    "$FIXED_PREDS"

echo "[3/3] Evaluating..."
python3 ../pipeline/evaluate.py \
    --preds "$FIXED_PREDS" \
    --gold "$DATA_PATH" \
    --output_dir "$EVAL_RESULTS"

echo "Done! check $EVAL_RESULTS/summary.json"
