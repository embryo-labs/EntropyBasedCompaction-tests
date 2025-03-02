#!/usr/bin/env sh
"$(dirname $0)"/dbbench-load.sh
"$(dirname $0)"/dbbench-run.sh 10MB/s 100MB/s
"$(dirname $0)"/../plot/dbbench-report.py ../../data/rocksdb
