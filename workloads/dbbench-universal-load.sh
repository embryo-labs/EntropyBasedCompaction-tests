#!/usr/bin/env sh
if [ ! "$4" ]; then
	echo Usage: "$0" output-dir num-unique-keys key-size value-size
	exit 1
fi
. "$(dirname $0)"/common.sh
with_policy_universal $(dirname "$0")/dbbench-load.sh "$@"
