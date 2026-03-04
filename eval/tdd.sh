# on the GPU node:
# CUDA_VISIBLE_DEVICES=0 python3 -m sglang.launch_server --model-path Qwen/Qwen3-4B-Instruct-2507 --served-model-name qwen34i --tensor-parallel-size 1 --data-parallel-size 1 --tool-call-parser qwen25 --mem-fraction-static 0.90 --host 0.0.0.0 --port 8001 --api-key swespot --context-length 48000

# on the evaluation node:
# VERSION=0 WORKERS=6 MS=qwen34i CONFIG=eval/tdd_host.yaml REPO=django HASH=e13b714 eval/tdd.sh

set -x

MS=${MS:-unknown}
MODEL=${MODEL:-openai/$MS}
MODEL_CLASS=${MODEL_CLASS:-litellm}
REPO=${REPO:-django}
HASH=${HASH:-e13b714}
VERSION=${VERSION:-1}
CONFIG=${CONFIG:-eval/tdd_host.yaml}
WORKERS=${WORKERS:-12}
RUN_EVAL=${RUN_EVAL:-true}

REPO_HASH=${REPO}_${HASH}
OUTPUT_DIR=eval_results/tdd/$REPO_HASH/$MS/v$VERSION
RUN_ID=tdd_${REPO_HASH}_${MS}_v${VERSION}

uv run mini-extra swebench -c $CONFIG --workers $WORKERS \
    --subset eval/data/tdd/$REPO.jsonl \
    --model $MODEL \
    --model-class $MODEL_CLASS \
    --remote-port-selection $PORT \
    --output $OUTPUT_DIR

if [ "$RUN_EVAL" = "true" ]; then
    docker ps -aq --filter "name=$RUN_ID" | xargs -r docker rm -f
    sleep 3s

    timeout 3h uv run python -m tddbench.harness.run_evaluation \
        --dataset_name eval/data/tdd/$REPO.jsonl \
        --predictions_path $OUTPUT_DIR/preds.json \
        --max_workers 16 \
        --run_id $RUN_ID \
        --cache_level instance

    mv logs/run_evaluation/$RUN_ID $OUTPUT_DIR/logs
    mv *$RUN_ID.json $OUTPUT_DIR/

    grep '"resolved": true' -r $OUTPUT_DIR/logs | wc -l | tee -a $OUTPUT_DIR/report.log
else
    echo 'skipping evaluation after generation'
fi
