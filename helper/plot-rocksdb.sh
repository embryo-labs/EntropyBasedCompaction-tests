#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: "$0" data-dir
	exit 1
fi
$(dirname $0)/../plot/du.py "$1"
$(dirname $0)/../plot/iostat.py "$1" 1
if [ -d "$1/load" ]; then
	$(dirname $0)/../plot/dbbench-report.py "$1/load"
	$(dirname $0)/../plot/op-count-time.py "$1/load"
fi
if [ -d "$1/warmup" ]; then
	$(dirname $0)/../plot/dbbench-report.py "$1/warmup"
	$(dirname $0)/../plot/op-count-time.py "$1/warmup"
fi
$(dirname $0)/../plot/dbbench-report.py "$1"
$(dirname $0)/../plot/op-count-time.py "$1"
if [ -f log.json ]; then
	$(dirname $0)/../plot/parse-json-log.py "$1"
fi
