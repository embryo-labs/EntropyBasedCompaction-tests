#!/usr/bin/env sh
if [ $# -lt 2 ]; then
	echo Usage: $0 output-dir benchmark_write_rate_limit args...
	exit 1
fi
output_dir=$1
shift
benchmark_write_rate_limit=$1
shift
$(dirname $0)/dbbench-run.sh "$output_dir" \
	"$(dirname $0)/dbbench-universal.sh" \
	"$benchmark_write_rate_limit" \
	--space_amplification_percent_limit_hard=50 \
	"$@"
