#!/usr/bin/env sh
if [ $# -lt 4 ]; then
	echo Usage: $0 output-dir num-unique-keys key-size args...
	exit 1
fi
output_dir=$1
shift
num_unique_keys=$1
shift
key_size=$1
shift
. $(dirname $0)/common.sh
workspace=$(realpath "$(dirname $0)"/../..)
mkdir -p "$output_dir"
cd "$output_dir"
"$workspace"/tests/helper/exe-while.sh . "$workspace"/tests/workloads/dbbench.sh . "$num_unique_keys" "$key_size" \
	--use_existing_db=true \
	--writes=$num_unique_keys \
	--finish_after_writes=1 \
	--statistics=true \
	--report_file=report.csv \
	--report_interval_seconds=1 \
	--histogram=true \
	"$@" \
	> stdout.txt
