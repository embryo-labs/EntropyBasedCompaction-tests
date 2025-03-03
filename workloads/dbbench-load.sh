#!/usr/bin/env sh
workspace=$(realpath "$(dirname $0)"/../..)
output_dir="$workspace/data/rocksdb"
mkdir -p "$output_dir"
if [ "$(ls -A "$output_dir")" ]; then
	echo "$output_dir" is not empty!
	exit 1
fi
rm "$workspace/testdb"/*
$(dirname $0)/dbbench.sh "$output_dir" \
	--benchmarks=filluniquerandomdeterministic,stats \
	--disable_auto_compactions=true \
	> "$output_dir"/load-stdout.txt
$(dirname $0)/dbbench-levelstats.sh
