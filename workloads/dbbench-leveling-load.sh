#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: "$0" output-dir
	exit 1
fi
$(dirname "$0")/dbbench-load.sh "$1" "$(dirname $0)/dbbench-leveling.sh"
