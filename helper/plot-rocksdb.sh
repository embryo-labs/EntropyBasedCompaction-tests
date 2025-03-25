#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: "$0" data-dir
	exit 1
fi
$(dirname $0)/../plot/iostat.py "$1" 1
$(dirname $0)/../plot/dbbench-report.py "$1"
$(dirname $0)/../plot/op-count-time.py "$1"
