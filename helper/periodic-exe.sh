#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: $0 output-dir
	exit
fi

DIR=$(realpath "$1")
mydir=$(dirname "$0")
cd "$mydir"/jobs-periodic
for work in $(ls); do
	if [ -x "$work" -a -f "$work" ]; then
		./"$work" "$DIR" &
	fi
done
# "wait -n" is not available in POSIX
trap 'exit 1' CHLD INT TERM
trap "echo periodic-exe: exiting... 1>&2; pkill -TERM -P $$" EXIT
wait
