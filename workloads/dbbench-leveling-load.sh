#!/usr/bin/env sh
workspace=$(realpath "$(dirname $0)"/../..)
output_dir="$workspace/data/rocksdb"
$(dirname "$0")/dbbench-load-deterministic.sh "$output_dir" "$(dirname $0)/dbbench-leveling.sh"
