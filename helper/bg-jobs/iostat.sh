#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: "$0" output-dir
	exit 1
fi
output_dir=$1
if [ ! "$db_dev" ]; then
	echo Environment variable \"db_dev\" is not set.
	exit 1
fi
if [ "$(iostat | grep "$db_dev")" = "" ]; then
	echo "$db_dev" does not exist in the output of iostat!
	exit 1
fi

echo Timestamp\(ns\) r/s rkB/s w/s wkB/s %util > "$output_dir"/iostat.txt

. $(dirname $0)/../modules/iostat.sh
iostat 1 -x | process "$db_dev" >> "$output_dir"/iostat.txt
