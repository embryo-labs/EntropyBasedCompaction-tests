#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: $0 output-dir command [[args]] 2>&1
	exit 1
fi

if [ ! -d "$1" ]; then
	mkdir -p "$1"
fi
output_dir="$1"
shift
cmd="$1"
shift
(
	setsid "$cmd" "$@" &
	trap "kill -TERM -$!" TERM
	wait
) &
"$(dirname $0)"/periodic-exe.sh $output_dir 1>&2 &
# "wait -n" is not available in POSIX
trap "exit 1" CHLD INT TERM
trap "pkill -P $$; exit 1" EXIT
wait
