#!/usr/bin/env sh
output_dir="$1"
workspace=$(realpath "$(dirname $0)"/../..)

rm "$workspace/testdb"/*
mkdir -p "$output_dir"
if [ "$(ls -A "$output_dir")" ]; then
	echo "$output_dir" is not empty!
	exit 1
fi
