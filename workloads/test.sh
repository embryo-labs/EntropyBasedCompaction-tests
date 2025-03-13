#!/usr/bin/env sh
test_rocksdb() {
	output_dir=../../data/bench-${2}MB-s-compaction-${3}MB-s/$1
	"$(dirname $0)"/dbbench-$1-load.sh "$output_dir" || exit $?
	"$(dirname $0)"/dbbench-$1-run.sh "$output_dir" ${2}MB ${3}MB
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../plot/dbbench-report.py "$output_dir"
}
test_custom() {
	output_dir=../../data/bench-${2}MB-s-compaction-${3}MB-s/$1
	"$(dirname $0)"/dbbench-load-L1.sh "$output_dir" || exit $?
	"$(dirname $0)"/dbbench-$1-run.sh "$output_dir" ${2}MB ${3}MB
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../plot/dbbench-report.py "$output_dir"
}
test_rocksdb leveling 40 400
test_rocksdb leveling 100 400
test_rocksdb universal 40 400
test_rocksdb universal 100 400
test_custom lazy-leveling 40 400
test_custom lazy-leveling 100 400
test_custom steady 40 400
test_custom steady 100 400
