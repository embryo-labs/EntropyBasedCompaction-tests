#!/usr/bin/env sh
if [ $# -lt 3 ]; then
	echo Usage: $0 output-dir num-unique-keys key-size args...
	exit 1
fi
output_dir=$1
shift
num_unique_keys=$1
shift
key_size=$1
shift

. $(dirname $0)/args.sh

$(dirname $0)/dbbench-run.sh "$output_dir" "$(dirname $0)"/dbbench.sh \
	"$num_unique_keys" "$key_size" \
	--compaction_style=5 \
	--compaction_policy="dynamic-tiering" \
	--C="$C" \
	--num_levels=3 \
	"$@"
