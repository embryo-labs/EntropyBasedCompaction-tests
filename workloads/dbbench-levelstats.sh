#!/usr/bin/env sh
workspace=$(realpath "$(dirname $0)"/../..)
output_dir="$workspace/data/rocksdb"
mkdir -p "$output_dir"
$(dirname $0)/dbbench.sh "$output_dir" \
	"--use_existing_db=true --benchmarks=levelstats" \
	> "$output_dir"/levelstats-load-finish 2>&1
