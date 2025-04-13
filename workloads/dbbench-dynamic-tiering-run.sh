#!/usr/bin/env sh
if [ $# -lt 2 ]; then
	echo Usage: $0 output-dir benchmark_write_rate_limit args...
	exit 1
fi
output_dir=$1
shift
benchmark_write_rate_limit=$(humanfriendly --parse-size="$1")
shift

. $(dirname $0)/args.sh

$(dirname $0)/dbbench-run.sh "$output_dir" "$(dirname $0)"/dbbench.sh \
	"$benchmark_write_rate_limit" \
	--compaction_style=5 \
	--compaction_policy="dynamic-tiering" \
	--C="$C" \
	--num_levels=3 \
	"$@"
