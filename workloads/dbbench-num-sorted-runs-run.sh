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
workspace=$(realpath "$(dirname $0)"/../..)

cd "$output_dir"
# disable_auto_compactions: make sure that no compaction happens
"$workspace"/tests/helper/exe-while.sh . \
	$workspace/tests/workloads/dbbench-num-sorted-runs.sh . "$num_unique_keys" "$key_size" "$num_sorted_runs" \
		--use_existing_db=true \
		--statistics=true \
		--report_file=report.csv \
		--report_interval_seconds=1 \
		--histogram=true \
		--duration=100 \
		--disable_auto_compactions=true \
		"$@" > stdout.txt
