#!/usr/bin/env sh
if [ $# -ne 2 ]; then
	echo Usage: $0 benchmark_write_rate_limit rate_limiter_bytes_per_sec
	exit 1
fi
workspace=$(realpath "$(dirname $0)"/../..)
output_dir="$workspace/data/rocksdb"
$(dirname $0)/dbbench-run.sh "$output_dir" "$(dirname $0)/dbbench-leveling.sh" "$1" "$2"
