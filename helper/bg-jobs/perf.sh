#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: "$0" output-dir main-pid
	exit 1
fi
output_dir=$1
main_pid=$2
sleep 1
perf record --pid=$main_pid --call-graph=fp --aio -z -o "$output_dir"/perf.data
