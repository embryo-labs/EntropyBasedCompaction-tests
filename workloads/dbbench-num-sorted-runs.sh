#!/usr/bin/env sh
if [ ! "$4" ]; then
	echo Usage: $0 output-dir num-unique-keys key-size num-sorted-runs args...
	exit 1
fi
output_dir=$1
shift
num_unique_keys=$1
shift
key_size=$1
shift
num_sorted_runs=$1
shift
. $(dirname $0)/args.sh

max_bytes_for_level_multiplier_additional=",1"
level=$((num_sorted_runs - 1))
size=$((R * C))
while [ $level -gt 0 ]; do
	if [ $size -ge $C ]; then
		size=$((size / C))
		v=$C
	else
		v=1
	fi
	max_bytes_for_level_multiplier_additional=",$v${max_bytes_for_level_multiplier_additional}"
	level=$((level - 1))
done
max_bytes_for_level_multiplier_additional="1${max_bytes_for_level_multiplier_additional}"

"$(dirname $0)"/dbbench.sh "$output_dir" "$num_unique_keys" "$key_size" \
	--num_levels=$((num_sorted_runs + 1)) \
	--max_bytes_for_level_base=$((unique_bytes / R / C)) \
	--max_bytes_for_level_multiplier=1 \
	--max_bytes_for_level_multiplier_additional="$max_bytes_for_level_multiplier_additional" \
	"$@"
