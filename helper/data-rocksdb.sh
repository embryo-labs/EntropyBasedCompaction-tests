#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: $0 output-dir
	exit 1
fi
output_dir=$(realpath "$1")
cd $(dirname $0)/../../testdb
mv LOG "$output_dir"
mv "$(ls OPTIONS-* | sort -n | tail -n1)" "$output_dir"
