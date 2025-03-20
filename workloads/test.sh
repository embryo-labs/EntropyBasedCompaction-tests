#!/usr/bin/env sh
test_rocksdb() {
	version=$1
	shift
	benchmark=$1
	shift
	write_MB_s=$1
	shift
	compaction_MB_s=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark-${write_MB_s}MB-s-compaction-${compaction_MB_s}MB-s/$version
	"$(dirname $0)"/dbbench-$version-load.sh "$output_dir" || exit $?
	"$(dirname $0)"/dbbench-$version-run.sh "$output_dir" \
		${write_MB_s}MB ${compaction_MB_s}MB \
		--benchmarks=$benchmark,resetstats,$benchmark,stats \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
}
test_custom() {
	version=$1
	shift
	benchmark=$1
	shift
	write_MB_s=$1
	shift
	compaction_MB_s=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark-${write_MB_s}MB-s-compaction-${compaction_MB_s}MB-s/$version
	"$(dirname $0)"/dbbench-load-L2.sh "$output_dir" || exit $?
	"$(dirname $0)"/dbbench-$version-run.sh "$output_dir" \
		${write_MB_s}MB ${compaction_MB_s}MB \
		--benchmarks=$benchmark,resetstats,$benchmark,stats \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
}

test_rocksdb leveling seekrandomwhilewriting 20 200
test_rocksdb universal seekrandomwhilewriting 20 200
test_custom lazy-leveling seekrandomwhilewriting 20 200
test_custom steady seekrandomwhilewriting 20 200
