#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: "$0" output-dir command args...
	exit 1
fi
output_dir=$1
shift
command=$1
shift
workspace=$(realpath "$(dirname $0)"/../..)
mkdir -p "$output_dir"
if [ "$(ls -A "$output_dir")" ]; then
	echo "$output_dir" is not empty!
	exit 1
fi
rm "$workspace/testdb"/*
$command "$output_dir" "$@" > "$output_dir"/load-stdout.txt
$(dirname $0)/dbbench-levelstats.sh "$output_dir"
