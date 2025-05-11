#!/usr/bin/env sh
if [ $# -lt 3 ]; then
	echo Usage: $0 output-dir num-unique-keys key-size args...
	exit 1
fi
. $(dirname $0)/common.sh

$(dirname $0)/dbbench-run.sh "$@" \
	--compaction_style=5 \
	--compaction_policy="dynamic-size-ratio" \
	--C="$C" \
	--num_levels=3
