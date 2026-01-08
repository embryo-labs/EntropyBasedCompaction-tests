#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: $0 output-dir main-pid
	exit
fi
output_dir=$(realpath "$1")
main_pid=$2

cd "$(dirname "$0")"/bg-jobs
./du.sh "$output_dir" &
./iostat.sh "$output_dir" &
if [ "$with_perf" ] && [ "$with_perf" -gt 0 ]; then
	./perf.sh "$output_dir" "$main_pid" &
fi

# "wait -n" is not available in POSIX
trap 'exit 1' CHLD INT TERM
trap "echo exe-bg-jobs: exiting... 1>&2; pkill -TERM -P $$" EXIT
wait
