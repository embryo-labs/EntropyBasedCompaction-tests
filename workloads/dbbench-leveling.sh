#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: "$0" output-dir args...
	exit 1
fi
output_dir=$1
shift
. $(dirname $0)/args.sh
$(dirname $0)/dbbench.sh "$output_dir" \
	--num_levels=5 \
	--level0_file_num_compaction_trigger=$s \
	--max_bytes_for_level_base=$(($memtable_size * $s)) \
	--max_bytes_for_level_multiplier=5 \
	"$@"
