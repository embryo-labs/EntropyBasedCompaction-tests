#!/usr/bin/env sh
test_rocksdb() (
	version=$1
	shift
	benchmark=$1
	shift
	write_MB_s=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark-${write_MB_s}MB-s$suffix/$version
	"$(dirname $0)"/dbbench-$version-load.sh "$output_dir" || exit $?
	"$(dirname $0)"/dbbench-$version-run.sh "$output_dir" \
		${write_MB_s}MB \
		--benchmarks=$benchmark,resetstats,$benchmark,stats \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)

test_three_levels() (
	version=$1
	shift
	benchmark=$1
	shift
	write_MB_s=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark-${write_MB_s}MB-s$suffix/$version
	"$(dirname $0)"/dbbench-load-L2.sh "$output_dir" || exit $?
	"$(dirname $0)"/dbbench-$version-run.sh "$output_dir" \
		${write_MB_s}MB \
		--benchmarks=$benchmark,resetstats,$benchmark,stats \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)

test_steady() (
	benchmark=$1
	shift
	write_MB_s=$1
	shift
	compaction_MB_s=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark-${write_MB_s}MB-s-compaction-${compaction_MB_s}MB-s$suffix/steady
	"$(dirname $0)"/dbbench-load-L2.sh "$output_dir" || exit $?
	"$(dirname $0)"/dbbench-steady-run.sh "$output_dir" \
		${write_MB_s}MB ${compaction_MB_s}MB \
		--benchmarks=$benchmark,resetstats,$benchmark,stats \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)

with_compaction_limit_MB_s() (
	compaction_MB_s=$1
	shift
	suffix="-compaction-${compaction_MB_s}MB-s$suffix" "$@" \
		--rate_limiter_bytes_per_sec=$(($compaction_MB_s * 1000000))
)

suffix="-threads-16" test_rocksdb leveling seekrandomwhilewriting 10 --threads=16
suffix="-threads-16" with_compaction_limit_MB_s 100 test_rocksdb leveling seekrandomwhilewriting 10 --threads=16

seek=1000
while [ "$seek" -le 20000 ]; do
	suffix="-threads-16-seek-$seek" test_rocksdb leveling queuedseekrandomwhilewriting 10 --threads=16 --benchmark_read_rate_limit=$seek
	suffix="-threads-16-seek-$seek" with_compaction_limit_MB_s 100 test_rocksdb leveling queuedseekrandomwhilewriting 10 --threads=16 --benchmark_read_rate_limit=$seek
	seek=$((seek + 1000))
done

bench=seekrandomwhilewriting
suffix="-threads-16"
args="--threads=16"

write=1
while [ "$write" -le 20 ]; do
	suffix="$suffix" with_compaction_limit_MB_s 100 test_rocksdb leveling "$bench" $write $args
	suffix="$suffix" with_compaction_limit_MB_s 100 test_rocksdb universal "$bench" $write $args
	suffix="$suffix" with_compaction_limit_MB_s 100 test_three_levels lazy-leveling "$bench" $write $args
	suffix="$suffix" with_compaction_limit_MB_s 100 test_three_levels dynamic-tiering "$bench" $write $args
	suffix="$suffix" test_steady "$bench" $write 100 $args
	write=$((write + 1))
done
