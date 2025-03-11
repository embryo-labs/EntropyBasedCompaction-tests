#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: "$0" output-dir args...
	exit 1
fi
output_dir=$1
shift
$(dirname $0)/dbbench.sh "$output_dir" \
	--compaction_style=1 \
	--universal_compaction_policy="lazy-leveling" \
	--num_levels=2 \
	"$@"
