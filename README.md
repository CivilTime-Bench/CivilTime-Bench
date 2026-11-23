# CivilTime-Benchmark

CivilTime-Benchmark is a comprehensive dataset and evaluation suite designed to assess the reasoning capabilities of Large Language Models (LLMs) on complex civil time systems. It covers a wide range of temporal tasks including timezone conversion, dateline arithmetic, DST transition handling, and business day calculations.

## Directory Structure

```text
CivilTime-Benchmark/
├── data/
│   ├── generator/       # Script to generate synthetic datasets
│   ├── 1M_full/         # Full 1 Million sample dataset
│   ├── 60k_train/       # Subsampled 60k dataset for finetuning
│   └── 10k_eval/        # 10k evaluation dataset
├── pipeline/
│   ├── run_inference.py # Unified inference script (Zero-shot, ICL)
│   ├── fix_format.py    # Post-processing script to normalize outputs
│   └── evaluate.py      # Metric calculation (Exact Match, Temporal Error)
├── finetune/
│   ├── train.py         # SFTTrainer script for finetuning models
│   └── utils.py         # Finetuning utilities
├── scripts/
│   └── run_full_pipeline.sh # Example bash script for end-to-end flow
└── requirements.txt
```

## Installation

```bash
cd CivilTime-Benchmark
pip install -r requirements.txt
```

## Usage

### 1. Data Generation

To generate a fresh dataset:

```bash
python data/generator/generate_data.py \
    --output custom_dataset.jsonl \
    --total 5000 \
    --seed 42
```

### 2. Evaluation Pipeline

The evaluation pipeline consists of three steps: **Inference -> Fix Format -> Evaluate**.

You can run them individually or use the provided script `scripts/run_full_pipeline.sh`.

#### Step 1: Inference
Run the model on the dataset. Supports Zero-shot and ICL.

```bash
python pipeline/run_inference.py \
    --model "Qwen/Qwen2.5-7B-Instruct" \
    --data "data/10k_eval/eval_10k.jsonl" \
    --output "results/raw_preds.jsonl" \
    --method zeroshot \
    --batch_size 8
```

For Few-shot (ICL), provide exemplars:
```bash
python pipeline/run_inference.py \
    ... \
    --method icl \
    --shots 2 \
    --exemplars_file "data/10k_eval/eval_10k.jsonl"
```

#### Step 2: Fix Format
Standardize the model's raw output to ISO-8601 format. This script handles common formatting issues and selects the best candidate answer.

```bash
python pipeline/fix_format.py \
    "results/raw_preds.jsonl" \
    "results/fixed_preds.jsonl"
```

#### Step 3: Evaluate
Compute accuracy (Exact Match) and Temporal Error.

```bash
python pipeline/evaluate.py \
    --preds "results/fixed_preds.jsonl" \
    --gold "data/10k_eval/eval_10k.jsonl" \
    --output_dir "results/metrics"
```

### 3. Finetuning

To finetune a model (e.g., Phi-4, Llama-3) on the 60k dataset:

```bash
python finetune/train.py \
    --model_name "microsoft/phi-4" \
    --data_path "data/60k_train/train_60k.jsonl" \
    --output_dir "models/phi4-civiltime" \
    --batch_size 2 \
    --grad_accum 16 \
    --epochs 1
```

Using 4-bit quantization (QLoRA) is supported via `--use_4bit`.

## Dataset Details

The benchmark includes tasks such as:
- **OFFSET**: Adding time with timezone offsets.
- **DST_SKIP**: Calculating time across "spring forward" gaps.
- **DST_AMBIG**: Handling ambiguous times during "fall back".
- **DATE_LINE**: Crossing the International Date Line.
- **BUSINESS_DAY**: Calculating business days skipping weekends.

See `data/generator/generate_data.py` for full logic.

## Citation

[Please insert your citation here]
