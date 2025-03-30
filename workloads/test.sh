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
	suffix=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark-${write_MB_s}MB-s-compaction-${compaction_MB_s}MB-s$suffix/$version
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
	suffix=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark-${write_MB_s}MB-s-compaction-${compaction_MB_s}MB-s$suffix/$version
	"$(dirname $0)"/dbbench-load-L2.sh "$output_dir" || exit $?
	"$(dirname $0)"/dbbench-$version-run.sh "$output_dir" \
		${write_MB_s}MB ${compaction_MB_s}MB \
		--benchmarks=$benchmark,resetstats,$benchmark,stats \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
}

test_rocksdb leveling readwhilewriting 1 10
test_rocksdb universal readwhilewriting 1 10
test_custom lazy-leveling readwhilewriting 1 10
test_custom steady readwhilewriting 1 10

test_custom lazy-leveling seekrandomwhilewriting 1 10 "-threads-16" --threads=16
test_custom lazy-leveling seekrandomwhilewriting 1 10 "-seek-5e2" --benchmark_read_rate_limit=500

suffix="-threads-16"
args="--threads=16"

write=1
while [ "$write" -le 20 ]; do
	test_rocksdb leveling seekrandomwhilewriting $write 100 "$suffix" $args
	test_rocksdb universal seekrandomwhilewriting $write 100 "$suffix" $args
	test_custom lazy-leveling seekrandomwhilewriting $write 100 "$suffix" $args
	test_custom steady seekrandomwhilewriting $write 100 "$suffix" $args
	write=$((write + 1))
done
