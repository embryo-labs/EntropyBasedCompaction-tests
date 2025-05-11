#!/usr/bin/env sh
if [ $# -lt 3 ]; then
	echo Usage: $0 output-dir num-unique-keys key-size args...
	exit 1
fi
. $(dirname $0)/common.sh
if [ "$s" -eq 1 ]; then
	lazy_leveling_num_sorted_runs=""
else
	lazy_leveling_num_sorted_runs="$s"
fi
T=2
size=1
while [ "$size" -lt "$R" ]; do
	size=$((size * T))
	if [ "$lazy_leveling_num_sorted_runs" ]; then
		lazy_leveling_num_sorted_runs="$lazy_leveling_num_sorted_runs,$T"
	else
		lazy_leveling_num_sorted_runs="$T"
	fi
done
echo "lazy_leveling_num_sorted_runs $lazy_leveling_num_sorted_runs"

$(dirname $0)/dbbench-run.sh "$@" \
	--compaction_style=5 \
	--compaction_policy="lazy-leveling" \
	--lazy_leveling_num_sorted_runs="$lazy_leveling_num_sorted_runs" \
	--num_levels=3
