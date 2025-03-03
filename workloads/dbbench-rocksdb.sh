#!/usr/bin/env sh
if ! "$(dirname $0)"/dbbench-load.sh; then
	exit 1
fi
"$(dirname $0)"/dbbench-run.sh 10MB/s 100MB/s
"$(dirname $0)"/../helper/data-rocksdb.sh ../../data/rocksdb
"$(dirname $0)"/../plot/dbbench-report.py ../../data/rocksdb
