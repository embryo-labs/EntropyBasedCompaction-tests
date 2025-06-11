#!/usr/bin/env sh
if [ $# -lt 3 ]; then
	echo Usage: $0 output-dir num-unique-keys key-size args...
	exit 1
fi
. $(dirname $0)/common.sh
$(dirname $0)/dbbench-run.sh "$@" \
	--compaction_style=4 \
	--compaction_policy="tiering" \
	--max_bytes_for_level_multiplier=2 \
	--num_levels=1
