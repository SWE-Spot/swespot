# 🔎 SWE-Spot

Environment Setup:

```bash
uv sync
```

## Evaluation

Benchmark datasets filtered with knowledge-cutoff protocol (after 2020-12-31):

```bash
❯ ls eval/data
fea  qa  sbv  tdd
```

mini-swe-agent config files for each task:

```bash
❯ ls eval | grep yaml
fea_host.yaml
qa_host.yaml
sbv_host.yaml
tdd_host.yaml
```

You need to change the LLM API information in these config files.

Evaluation scripts for the four tasks:

```bash
❯ ls eval | grep sh
sbv.sh # SWE-Bench-Verified
tdd.sh # TDD-Bench-Verified
fea.sh # FEA-Bench
qa.sh # SWE-QA
```

Take a look at each to know how to specify the arguments with environment variables, like:

```bash
VERSION=0 WORKERS=6 MS=qwen34i CONFIG=eval/sbv_host.yaml REPO=django HASH=e13b714 eval/sbv.sh
```

## SFT

TBD

## Data Synthesis

TBD
