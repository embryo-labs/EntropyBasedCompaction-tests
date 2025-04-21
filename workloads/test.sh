#!/usr/bin/env sh
. $(dirname $0)/args.sh

bench_num_sorted_runs() (
	benchmark=$1
	shift
	key_size=$1
	shift
	load_value_size=$1
	shift
	num_sorted_runs=$1
	shift
	output_dir=../../data/$benchmark-sorted-runs-$num_sorted_runs$suffix/leveling
	num_unique_keys=$((unique_bytes / (key_size + load_value_size)))
	workspace=$(realpath "$(dirname $0)"/../..)

	../helper/build.sh

	mkdir -p "$output_dir"
	if [ "$(ls -A "$output_dir")" ]; then
		echo "$output_dir" is not empty!
		exit 1
	fi
	rm "$workspace/testdb"/*
	"$(dirname $0)"/dbbench-num-sorted-runs.sh "$output_dir" "$num_unique_keys" "$key_size" "$num_sorted_runs" \
		--value_size="$load_value_size" \
		--benchmarks=filluniquerandomdeterministic,compact0,stats \
		--disable_auto_compactions=true > "$output_dir"/load-stdout.txt
	ret=$?
	mv "$workspace"/testdb/LOG "$output_dir"/load-LOG
	if [ $ret -ne 0 ]; then
		exit $ret
	fi
	$(dirname $0)/dbbench-num-sorted-runs-run.sh "$output_dir" "$num_unique_keys" "$key_size" "$num_sorted_runs" \
		--benchmarks=$benchmark,stats \
		"$@"
	$workspace/tests/helper/data-rocksdb.sh "$output_dir"
	$workspace/tests/helper/plot-rocksdb.sh "$output_dir"
)

num_sorted_runs_mergerandom_readrandom() (
	key_size=$1
	shift
	load_value_size=$1
	shift
	num_sorted_runs=$1
	shift
	output_dir=../../data/mergerandom-readrandom-sorted-runs-$num_sorted_runs$suffix/leveling
	num_unique_keys=$((unique_bytes / (key_size + load_value_size)))
	workspace=$(realpath "$(dirname $0)"/../..)

	../helper/build.sh

	mkdir -p "$output_dir"
	if [ "$(ls -A "$output_dir")" ]; then
		echo "$output_dir" is not empty!
		exit 1
	fi
	rm "$workspace/testdb"/*
	"$(dirname $0)"/dbbench-num-sorted-runs.sh "$output_dir" "$num_unique_keys" "$key_size" "$num_sorted_runs" \
		--value_size="$load_value_size" \
		--benchmarks=filluniquerandomdeterministic,compact0,stats \
		--disable_auto_compactions=true \
		--merge_operator="BytesXOR" > "$output_dir"/load-stdout.txt
	ret=$?
	mv "$workspace"/testdb/LOG "$output_dir"/load-LOG
	if [ $ret -ne 0 ]; then
		exit $ret
	fi
	"$(dirname $0)"/dbbench-num-sorted-runs-run.sh "$output_dir" "$num_unique_keys" "$key_size" "$num_sorted_runs" \
		--benchmarks=readrandom,stats \
		--merge_operator="BytesXOR" \
		"$@"
	$workspace/tests/helper/data-rocksdb.sh "$output_dir"
	$workspace/tests/helper/plot-rocksdb.sh "$output_dir"
)

num_sorted_runs=100
while [ $num_sorted_runs -le 100 ]; do
	suffix="-threads-16" bench_num_sorted_runs seekrandom 24 1000 $num_sorted_runs --threads=16
	suffix="-threads-16" bench_num_sorted_runs readrandom 24 1000 $num_sorted_runs --threads=16
	suffix="-threads-16" num_sorted_runs_mergerandom_readrandom 24 1000 $num_sorted_runs --threads=16
	num_sorted_runs=$((num_sorted_runs + 1))
done

test_rocksdb() (
	version=$1
	shift
	benchmark=$1
	shift
	key_size=$1
	shift
	load_value_size=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark$suffix/$version
	num_unique_keys=$((unique_bytes / (key_size + load_value_size)))
	"$(dirname $0)"/dbbench-$version-load.sh "$output_dir" "$num_unique_keys" "$key_size" "$load_value_size" || exit $?
	"$(dirname $0)"/dbbench-$version-run.sh "$output_dir" "$num_unique_keys" "$key_size" \
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
	key_size=$1
	shift
	load_value_size=$1
	shift
	../helper/build.sh
	output_dir=../../data/$benchmark$suffix/$version
	num_unique_keys=$((unique_bytes / (key_size + load_value_size)))
	"$(dirname $0)"/dbbench-load-L2.sh "$output_dir" "$num_unique_keys" "$key_size" "$load_value_size" || exit $?
	"$(dirname $0)"/dbbench-$version-run.sh "$output_dir" "$num_unique_keys" "$key_size" \
		--benchmarks=$benchmark,stats \
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
	"$(dirname $0)"/dbbench-load-L2.sh "$output_dir" $((unique_bytes / (24 + 1000))) 24 1000 || exit $?
	"$(dirname $0)"/dbbench-steady-run.sh "$output_dir" \
		24 ${write_MB_s}MB ${compaction_MB_s}MB \
		--benchmarks=$benchmark,resetstats,$benchmark,stats \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)

with_bgwrite_MB_s() (
	bgwrite_MB_s=$1
	shift
	suffix="-write-${bgwrite_MB_s}MB-s$suffix" "$@" \
		--benchmark_write_rate_limit=$((bgwrite_MB_s * 1000000))
)
with_compaction_limit_MB_s() (
	compaction_MB_s=$1
	shift
	suffix="-compaction-${compaction_MB_s}MB-s$suffix" "$@" \
		--rate_limiter_bytes_per_sec=$(($compaction_MB_s * 1000000))
)

suffix="-threads-16" with_bgwrite_MB_s 10 test_rocksdb leveling seekrandomwhilewriting 24 1000 --threads=16
suffix="-threads-16" with_bgwrite_MB_s 10 with_compaction_limit_MB_s 100 test_rocksdb leveling seekrandomwhilewriting 24 1000 --threads=16

seek=1000
while [ "$seek" -le 20000 ]; do
	suffix="-threads-16-seek-$seek" with_bgwrite_MB_s 10 test_rocksdb leveling queuedseekrandomwhilewriting 24 1000 --threads=16 --benchmark_read_rate_limit=$seek
	suffix="-threads-16-seek-$seek" with_bgwrite_MB_s 10 with_compaction_limit_MB_s 100 test_rocksdb leveling queuedseekrandomwhilewriting 24 1000 --threads=16 --benchmark_read_rate_limit=$seek
	seek=$((seek + 1000))
done

bench=seekrandomwhilewriting
suffix="-threads-16"
args="--threads=16"

write=1
while [ "$write" -le 20 ]; do
	suffix="$suffix" with_bgwrite_MB_s $write with_compaction_limit_MB_s 100 test_rocksdb leveling "$bench" 24 1000 $args
	suffix="$suffix" with_bgwrite_MB_s $write with_compaction_limit_MB_s 100 test_rocksdb universal "$bench" 24 1000 $args
	suffix="$suffix" with_bgwrite_MB_s $write with_compaction_limit_MB_s 100 test_three_levels lazy-leveling "$bench" 24 1000 $args
	suffix="$suffix" with_bgwrite_MB_s $write with_compaction_limit_MB_s 100 test_three_levels dynamic-tiering "$bench" 24 1000 $args
	suffix="$suffix" test_steady "$bench" $write 100 $args
	write=$((write + 1))
done
