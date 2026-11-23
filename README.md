<p align="center">
  <h1 align="center">🗓️ CivilTime-Bench</h1>
  <p align="center">
    <b>When 1+1&nbsp;≠&nbsp;2:</b> Benchmarking Civil-Time Reasoning in Large Language Models
  </p>
  <p align="center">
    Official code and data release for the EACL 2027 Findings paper.
  </p>
</p>

<p align="center">
  <a href="https://github.com/CivilTime-Bench/CivilTime-Bench">
    <img src="https://img.shields.io/badge/GitHub-CivilTime--Bench-181717?logo=github" alt="GitHub">
  </a>
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Apache 2.0">
  <img src="https://img.shields.io/badge/Venue-EACL%202027%20Findings-b31b1b" alt="EACL 2027 Findings">
  <img src="https://img.shields.io/badge/Train-60%2C011-8E3D52" alt="Training size">
  <img src="https://img.shields.io/badge/Eval-10%2C500-C47A62" alt="Evaluation size">
  <img src="https://img.shields.io/github/stars/CivilTime-Bench/CivilTime-Bench?style=social" alt="GitHub stars">
  <img src="https://visitor-badge.laobi.icu/badge?page_id=CivilTime-Bench.CivilTime-Bench" alt="visitors">
</p>

---

## 📌 About this repository

This repository is the **official companion artifact** of the paper

> Melika Shirian, Kianoosh Vadaei, Arshia Hemmat, Mohammad Hossein Shaker Ardakani, Ali Mamanpoosh, Matin Moqadas, Amirmasoud Rismanchian, and Afsaneh Fatemi.  
> *When 1+1 ≠ 2: Benchmarking Civil-Time Reasoning in Large Language Models.*  
> **Findings of the Association for Computational Linguistics: EACL 2027.**

Please cite **the paper**, not this README, whenever you use the benchmark, splits, or scorer.

Civil time is non-linear. Adding one minute at a daylight-saving spring-forward can skip an hour; fall-back can repeat a wall-clock time; non-hour offsets, date-line crossings, and ISO week boundaries further break naive arithmetic. CivilTime-Bench evaluates whether language models can produce **machine-checkable** answers under a strict output contract, separating **format compliance** from **calendrical correctness**.

| Split | Size | Role |
| :--- | ---: | :--- |
| SyntheticTimeBench train | 60,011 | QLoRA fine-tuning |
| SyntheticTimeBench eval | 10,000 | Open-weight evaluation (API models use a 1,000-item subset) |
| HumanTime-500 | 500 | LLM-authored, human-validated transfer set (evaluation only) |

Training and synthetic evaluation **share generators** but use disjoint items. HumanTime-500 is held out for more naturalistic language.

---

## ✏️ Hand-drawn look at the paper result

QLoRA raises synthetic exact match to **74.6–86.6%**, but HumanTime-500 remains **36.6–45.2%** for models with valid results on both splits. Gemma’s HumanTime-500 fine-tuning dump is invalid and is omitted.

<p align="center">
  <img
    src="https://quickchart.io/chart?w=780&h=360&bkg=white&f=png&c=%7B%22type%22%3A%22bar%22%2C%22data%22%3A%7B%22labels%22%3A%5B%22Gemma-2-9B%22%2C%22LLaMA-3.1-8B%22%2C%22Mistral-7B%22%2C%22Phi-4-14B%22%5D%2C%22datasets%22%3A%5B%7B%22label%22%3A%22SyntheticTimeBench%20FT%20EM%20%28%25%29%22%2C%22data%22%3A%5B74.6%2C86.6%2C81.4%2C74.6%5D%2C%22backgroundColor%22%3A%22rgba%28142%2C%2061%2C%2082%2C%200.55%29%22%2C%22borderColor%22%3A%22%238E3D52%22%2C%22borderWidth%22%3A2%7D%2C%7B%22label%22%3A%22HumanTime-500%20FT%20EM%20%28%25%29%22%2C%22data%22%3A%5Bnull%2C39.6%2C45.2%2C36.6%5D%2C%22backgroundColor%22%3A%22rgba%28243%2C%20201%2C%20168%2C%200.75%29%22%2C%22borderColor%22%3A%22%23C47A62%22%2C%22borderWidth%22%3A2%7D%5D%7D%2C%22options%22%3A%7B%22legend%22%3A%7B%22position%22%3A%22bottom%22%7D%2C%22title%22%3A%7B%22display%22%3Atrue%2C%22text%22%3A%22CivilTime-Bench%20%20%7C%20%20QLoRA%20exact%20match%20%20%28paper%20results%29%22%2C%22fontSize%22%3A14%7D%2C%22plugins%22%3A%7B%22rough%22%3A%7B%22roughness%22%3A1.55%2C%22bowing%22%3A1.15%2C%22fillStyle%22%3A%22hachure%22%2C%22hachureGap%22%3A3.2%7D%7D%2C%22scales%22%3A%7B%22yAxes%22%3A%5B%7B%22ticks%22%3A%7B%22min%22%3A0%2C%22max%22%3A100%2C%22stepSize%22%3A20%7D%2C%22scaleLabel%22%3A%7B%22display%22%3Atrue%2C%22labelString%22%3A%22Exact%20Match%20%28%25%29%22%7D%7D%5D%7D%7D%7D"
    alt="Hand-drawn bar chart of QLoRA exact match on SyntheticTimeBench versus HumanTime-500"
    width="780">
</p>

<p align="center"><i>Rough.js / QuickChart rendering of the camera-ready fine-tuning numbers. Gemma HumanTime-500 is left blank on purpose.</i></p>

---

## 📁 Repository layout

```text
CivilTime-Bench/
├── data/
│   ├── generator/          # Synthetic generators
│   ├── 60k_train/          # Fine-tuning split (paper: 60,011)
│   ├── 10k_eval/           # Synthetic evaluation split (paper: 10,000)
│   └── 1M_full/            # Larger synthetic pool (not used in the paper tables)
├── pipeline/
│   ├── run_inference.py    # Zero-shot and ICL inference
│   ├── fix_format.py       # Surface-form normalisation
│   └── evaluate.py         # Exact match and temporal-error diagnostics
├── finetune/
│   ├── train.py            # QLoRA / SFT training
│   └── utils.py
├── scripts/
│   └── run_full_pipeline.sh
├── LICENSE                 # Apache License 2.0
└── requirements.txt
```

---

## 🧩 Output contract

Each gold answer is one of five canonical forms:

1. `ABSTAIN` — no valid instant under the stated policy  
2. `YYYY-MM-DD` or `YYYY-Www` — date or ISO week label  
3. `YYYY-MM-DDThh:mm:ss±hh:mm` (or `Z`) — timestamp with explicit offset  
4. `A||B` — ambiguity pair (DST fall-back)  
5. `A..B` — half-open interval `[A, B)`

**Scoring.** Exact Match is strict equality after label-agnostic canonicalisation. FormatOK measures whether the extracted answer is one of the five forms. ContractOK scores the raw completion. A zero Median Temporal Error does **not** mean error-free performance over the full split.

Synthetic INTERVAL gold is stored as `A||B`; HumanTime-500 uses `A..B`. The scorer treats `..` and `||` as equivalent after canonicalisation.

---

## 🧪 Task types

DST skip / repeat / ambiguity, non-hour offsets, date-line conversion, ISO week, business-day arithmetic, relative day, constraints, intervals, and (on HumanTime-500 and the API 1k subset) week-start.

---

## ⚙️ Setup

```bash
git clone https://github.com/CivilTime-Bench/CivilTime-Bench.git
cd CivilTime-Bench
pip install -r requirements.txt
```

---

## 🚀 Usage

### Inference

```bash
python pipeline/run_inference.py \
  --model "Qwen/Qwen2.5-7B-Instruct" \
  --data "data/10k_eval/eval_10k.jsonl" \
  --output "results/raw_preds.jsonl" \
  --method zeroshot \
  --batch_size 8
```

Few-shot ICL (`k ∈ {2,4,8}`), type-matched exemplars from the training split:

```bash
python pipeline/run_inference.py \
  --model "Qwen/Qwen2.5-7B-Instruct" \
  --data "data/10k_eval/eval_10k.jsonl" \
  --output "results/raw_preds.jsonl" \
  --method icl \
  --shots 2 \
  --exemplars_file "data/60k_train/train_60k.jsonl"
```

### Normalise and score

```bash
python pipeline/fix_format.py \
  "results/raw_preds.jsonl" \
  "results/fixed_preds.jsonl"

python pipeline/evaluate.py \
  --preds "results/fixed_preds.jsonl" \
  --gold "data/10k_eval/eval_10k.jsonl" \
  --output_dir "results/metrics"
```

Missing predictions are counted as incorrect against the full gold split.

### Fine-tuning (QLoRA)

```bash
python finetune/train.py \
  --model_name "meta-llama/Llama-3.1-8B" \
  --data_path "data/60k_train/train_60k.jsonl" \
  --output_dir "models/llama-civiltime" \
  --batch_size 2 \
  --grad_accum 16 \
  --epochs 1 \
  --use_4bit
```

The paper fine-tunes five open-weight models; Llama-3.1-8B is the **base** checkpoint, not Instruct. Table 6 reports the four models with matched synthetic evaluation. Gemma’s HumanTime-500 fine-tuning dump is excluded; Qwen’s 10k fine-tuning IDs do not match the gold split.

---

## 📚 Citation

This GitHub repository distributes the artifacts of the following paper. If you use CivilTime-Bench, please cite:

```bibtex
@inproceedings{shirian2027civiltime,
  title     = {When 1+1 $\neq$ 2: Benchmarking Civil-Time Reasoning in Large Language Models},
  author    = {Shirian, Melika and Vadaei, Kianoosh and Hemmat, Arshia
               and Shaker Ardakani, Mohammad Hossein and Mamanpoosh, Ali
               and Moqadas, Matin and Rismanchian, Amirmasoud and Fatemi, Afsaneh},
  booktitle = {Findings of the Association for Computational Linguistics: EACL 2027},
  year      = {2027}
}
```

A camera-ready anthology ID / DOI will be added here when the proceedings are published.

---

## ⚖️ License

Code and dataset in this repository are released under the [Apache License 2.0](LICENSE).  
Third-party model checkpoints remain subject to their own licenses and terms of use.

The data are synthetically generated (HumanTime-500: fictionalized, LLM-authored scenarios with human validation) and do not contain real user logs or personally identifiable information.

---

## ⚠️ Intended use

Research and education on civil-time reasoning and evaluation methodology. Benchmark scores are **not** certification for medical scheduling, financial settlement, legal deadlines, or forensic timeline reconstruction.
