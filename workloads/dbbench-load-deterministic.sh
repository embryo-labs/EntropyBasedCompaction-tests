#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: "$0" output-dir command
	exit 1
fi
output_dir=$1
command=$2
$(dirname "$0")/dbbench-load.sh "$output_dir" $command \
	--benchmarks=filluniquerandomdeterministic,stats \
	--disable_auto_compactions=true
