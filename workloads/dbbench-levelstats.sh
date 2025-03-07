#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: "$0" output-dir
	exit 1
fi
workspace=$(realpath "$(dirname $0)"/../..)
output_dir=$1
mkdir -p "$output_dir"
$(dirname $0)/dbbench.sh "$output_dir" \
	--use_existing_db=true \
	--benchmarks=levelstats \
	> "$output_dir"/levelstats-load-finish 2>&1
