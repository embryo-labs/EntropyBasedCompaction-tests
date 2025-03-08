#!/usr/bin/env sh
test_policy() {
	output_dir=../../data/bench-${2}MB-s-compaction-${3}MB-s/$1
	if ! "$(dirname $0)"/dbbench-$1-load.sh "$output_dir"; then
		return 1
	fi
	"$(dirname $0)"/dbbench-$1-run.sh "$output_dir" ${2}MB ${3}MB
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../plot/dbbench-report.py "$output_dir"
}
test_policy leveling 40 400
