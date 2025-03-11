#!/usr/bin/env sh
if [ $# -ne 3 ]; then
	echo Usage: $0 output-dir benchmark_write_rate_limit rate_limiter_bytes_per_sec
	exit 1
fi
$(dirname $0)/dbbench-run.sh "$1" "$(dirname $0)"/dbbench-lazy-leveling.sh "$2" "$3"
