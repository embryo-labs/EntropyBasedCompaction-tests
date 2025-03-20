#!/usr/bin/env sh
if [ $# -lt 3 ]; then
	echo Usage: $0 output-dir benchmark_write_rate_limit rate_limiter_bytes_per_sec args...
	exit 1
fi
output_dir=$1
shift
benchmark_write_rate_limit=$1
shift
rate_limiter_bytes_per_sec=$1
shift
$(dirname $0)/dbbench-run.sh "$output_dir" \
	"$(dirname $0)/dbbench-universal.sh" \
	"$benchmark_write_rate_limit" "$rate_limiter_bytes_per_sec" \
	--space_amplification_percent_limit_hard=50 \
	"$@"
