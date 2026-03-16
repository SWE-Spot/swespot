#!/bin/bash

set -ex

export TYPE=mix
export RUN_NAME=8k_django_qwen34i_v0
export OUTPUT_DIR=train/outputs/$TYPE/$RUN_NAME
export CUDA_VISIBLE_DEVICES=0,1
export NPROC_PER_NODE=2

export DATA_DIR=/path/to/swespot-sft-v0-hf-repo

export OMP_NUM_THREADS=16
export PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True'

mkdir -p train/outputs/$TYPE train/logs/$TYPE

script -c '
megatron sft \
    --finetune true \
    --model Qwen/Qwen3-4B-Instruct-2507 \
    --train_type full \
    --split_dataset_ratio 0.00 \
    --dataset \
    $DATA_DIR/data/software_design/django.jsonl#2048 \
    $DATA_DIR/data/ctx_impl/django.jsonl#2048 \
    $DATA_DIR/data/evo_replay/django.jsonl#2048 \
    $DATA_DIR/data/rt_alignment/django.jsonl#2048 \
    --max_length 32768 \
    --truncation_strategy left \
    --loss_scale default \
    --load_from_cache_file true \
    --micro_batch_size 1 \
    --global_batch_size 16 \
    --max_epochs 2 \
    --save_interval 512 \
    --eval_interval 256 \
    --lr 1e-5 \
    --lr_decay_style cosine \
    --min_lr 1e-6 \
    --lr_warmup_fraction 0.03 \
    --tensor_model_parallel_size 1 \
    --recompute_granularity full \
    --recompute_method uniform \
    --recompute_num_layers 1 \
    --use-distributed-optimizer true \
    --save $OUTPUT_DIR \
    --log_interval 1 \
    --no_save_optim true \
    --no_save_rng true \
    --wandb_project swespot \
    --wandb_exp_name $RUN_NAME \
    --overlap_grad_reduce true \
    --overlap_param_gather true \
    --cross_entropy_loss_fusion true \
    --packing false \
    --num_workers 16 \
    --dataset_num_proc 16 \
    --attention_backend flash \
    --distributed_backend nccl \
    --load_safetensors true \
    --save_safetensors true \
    --use_hf true \
' train/logs/$TYPE/$RUN_NAME.log
