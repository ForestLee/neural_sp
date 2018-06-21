#!/bin/bash

. ./path.sh
set -e

### Select GPU
if [ $# -ne 2 ]; then
  echo "Error: set GPU number & config path." 1>&2
  echo "Usage: ./plot_ctc.sh path_to_saved_model gpu_id" 1>&2
  exit 1
fi

### Set path to save dataset
data=/n/sd8/inaguma/corpus/wsj/kaldi

CUDA_VISIBLE_DEVICES=$2 ${PYTHON} exp/visualization/plot_ctc_probs.py \
  --data_save_path ${data} \
  --model_path $1 \
  --epoch -1 \
  --eval_batch_size 1