# 🔎 SWE-Spot

<p align="center">
    <a href="https://arxiv.org/abs/2601.21649"><img src="https://img.shields.io/badge/arXiv-2601.21649-b31b1b.svg?style=for-the-badge">
    <a href="https://huggingface.co/swespot/"><img src="https://img.shields.io/badge/🤗%20Hugging%20Face-swespot-%23ff8811.svg?style=for-the-badge">
</p>

## Evaluation

Environment Setup:

```bash
uv sync
```

In general, the evaluation can be done by:
- Obtain the benchmark datasets for the four tasks.
- Change the LLM API information in mini-swe-agent config files. You can either query an existing endpoint or host one yourself.
- For any benchmark dataset, use mini-swe-agent to finish the instances, i.e., generating the trajectories.
- Run the corresponding evaluation harness to score the answers parsed from the trajectories.

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

[`ms-swift`](https://github.com/modelscope/ms-swift) is leveraged to perform SFT in our experiments. But of course, you can use other libraries to do SFT.

To use `ms-swift`, it is recommended to:
- Create a new Python environment dedicated to `ms-swift`. (Not the one used for evaluation.)
- Setup `ms-swift` in the environment:
  - https://swift.readthedocs.io/en/latest/GetStarted/SWIFT-installation.html
  - https://github.com/modelscope/ms-swift/blob/main/requirements/install_all.sh
  - https://github.com/Dao-AILab/flash-attention
  - https://swift.readthedocs.io/en/latest/Megatron-SWIFT/Quick-start.html

An example script for training the Django expert model: `train/mix_django.sh`
- The 4-unit RCX dataset is used for training. For each unit, we sample 2k instances, so the total training dataset is 8k instances. See the argument `--dataset` in the script.
- The dataset is available at https://huggingface.co/datasets/swespot/sft-v0 . Clone it somewhere, and set the environment variable `DATA_DIR` to the path of the cloned dataset in the script: `export DATA_DIR=/path/to/swespot-sft-v0-hf-repo` .
- Similarly, you can train expert models for other repositories.

Example trained models for the seven selected repositories in the paper can be found at [Hugging Face](https://huggingface.co/swespot/models), such as https://huggingface.co/swespot/django-sft-v0 .
