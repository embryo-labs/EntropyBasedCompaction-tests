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
if [ "$s" -eq 1 ]; then
	lazy_leveling_num_sorted_runs=""
else
	lazy_leveling_num_sorted_runs="$s"
fi
size=1
while [ "$size" -lt "$R" ]; do
	size=$((size * C))
	if [ "$lazy_leveling_num_sorted_runs" ]; then
		lazy_leveling_num_sorted_runs="$lazy_leveling_num_sorted_runs,$C"
	else
		lazy_leveling_num_sorted_runs="$C"
	fi
done

$(dirname $0)/dbbench-run.sh "$output_dir" "$(dirname $0)"/dbbench.sh \
	"$benchmark_write_rate_limit" \
	--compaction_style=5 \
	--compaction_policy="lazy-leveling" \
	--lazy_leveling_num_sorted_runs="$lazy_leveling_num_sorted_runs" \
	--num_levels=3 \
	"$@"
