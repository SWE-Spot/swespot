# on the GPU node:
# CUDA_VISIBLE_DEVICES=0 python3 -m sglang.launch_server --model-path Qwen/Qwen3-4B-Instruct-2507 --served-model-name qwen34i --tensor-parallel-size 1 --data-parallel-size 1 --tool-call-parser qwen25 --mem-fraction-static 0.90 --host 0.0.0.0 --port 8001 --api-key swespot --context-length 48000

# on the evaluation node:
# VERSION=0 WORKERS=6 MS=qwen34i CONFIG=eval/sbv_host.yaml REPO=django HASH=e13b714 eval/sbv.sh

set -x

MS=${MS:-unknown}
MODEL=${MODEL:-openai/$MS}
MODEL_CLASS=${MODEL_CLASS:-litellm}
REPO=${REPO:-django}
HASH=${HASH:-e13b714}
VERSION=${VERSION:-1}
CONFIG=${CONFIG:-eval/sbv_host.yaml}
WORKERS=${WORKERS:-12}
RUN_EVAL=${RUN_EVAL:-true}

REPO_HASH=${REPO}_${HASH}
OUTPUT_DIR=eval_results/sbv/$REPO_HASH/$MS/v$VERSION
RUN_ID=sbv_${REPO_HASH}_${MS}_v${VERSION}

uv run mini-extra swebench -c $CONFIG --workers $WORKERS \
    --subset eval/data/sbv/$REPO.jsonl \
    --model $MODEL \
    --model-class $MODEL_CLASS \
    --remote-port-selection $PORT \
    --output $OUTPUT_DIR

if [ "$RUN_EVAL" = "true" ]; then
    docker ps -aq --filter "name=$RUN_ID" | xargs -r docker rm -f
    sleep 3s

    uv run python -m swebench.harness.run_evaluation \
        --dataset_name princeton-nlp/SWE-bench_Verified \
        --predictions_path $OUTPUT_DIR/preds.json \
        --timeout 600 \
        --max_workers 12 \
        --run_id $RUN_ID

    mv logs/run_evaluation/$RUN_ID $OUTPUT_DIR/logs
    mv *$RUN_ID.json $OUTPUT_DIR/

    grep _instances $OUTPUT_DIR/*$RUN_ID.json | tee -a $OUTPUT_DIR/report.log
else
    echo 'skipping evaluation after generation'
fi
