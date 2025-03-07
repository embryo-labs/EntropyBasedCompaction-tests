#!/usr/bin/env sh
test_policy() {
	if ! "$(dirname $0)"/dbbench-$1-load.sh; then
		return 1
	fi
	"$(dirname $0)"/dbbench-$1-run.sh 40MB/s 400MB/s
	"$(dirname $0)"/../helper/data-rocksdb.sh ../../data/rocksdb
	"$(dirname $0)"/../plot/dbbench-report.py ../../data/rocksdb
}
test_policy leveling
