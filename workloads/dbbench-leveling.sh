#!/usr/bin/env sh
if [ ! "$3" ]; then
	echo Usage: "$0" output-dir num-unique-keys key-size args...
	exit 1
fi
output_dir=$1
shift
num_unique_keys=$1
shift
key_size=$1
shift
. $(dirname $0)/args.sh
$(dirname $0)/dbbench.sh "$output_dir" "$num_unique_keys" "$key_size" \
	--level_compaction_dynamic_level_bytes=true \
	--level0_file_num_compaction_trigger=$s \
	--max_bytes_for_level_multiplier=$C \
	"$@"
