# on the GPU node:
# CUDA_VISIBLE_DEVICES=0 python3 -m sglang.launch_server --model-path Qwen/Qwen3-4B-Instruct-2507 --served-model-name qwen34i --tensor-parallel-size 1 --data-parallel-size 1 --tool-call-parser qwen25 --mem-fraction-static 0.90 --host 0.0.0.0 --port 8001 --api-key swespot --context-length 48000

# on the evaluation node:
# export OPENAI_API_KEY=sk-your-key
# VERSION=0 WORKERS=6 MS=qwen34i CONFIG=eval/qa_host.yaml REPO=django HASH=e13b714 eval/qa.sh

set -x

MS=${MS:-unknown}
MODEL=${MODEL:-openai/$MS}
MODEL_CLASS=${MODEL_CLASS:-litellm}
REPO=${REPO:-django}
HASH=${HASH:-e13b714}
VERSION=${VERSION:-1}
CONFIG=${CONFIG:-eval/qa_host.yaml}
WORKERS=${WORKERS:-12}
RUN_EVAL=${RUN_EVAL:-true}

REPO_HASH=${REPO}_${HASH}
OUTPUT_DIR=eval_results/qa/$REPO_HASH/$MS/v$VERSION
RUN_ID=qa_${REPO_HASH}_${MS}_v${VERSION}

uv run mini-extra swebench -c $CONFIG --workers $WORKERS \
    --subset eval/data/qa/$REPO.jsonl \
    --model $MODEL \
    --model-class $MODEL_CLASS \
    --remote-port-selection $PORT \
    --output $OUTPUT_DIR

if [ "$RUN_EVAL" = "true" ]; then
    uv run eval/qa.py run --repo_name $REPO --eval_dir $OUTPUT_DIR --num_workers 8
else
    echo 'skipping evaluation after generation'
fi
