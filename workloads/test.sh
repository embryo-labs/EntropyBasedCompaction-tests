#!/usr/bin/env sh
. $(dirname $0)/common.sh

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
		--value_size="$load_value_size" \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)

test_three_levels() (
	workload_name=$1
	shift
	version=$1
	shift
	benchmark=$1
	shift
	key_size=$1
	shift
	load_value_size=$1
	shift
	../helper/build.sh
	output_dir=../../data/$workload_name/$version
	num_unique_keys=$((unique_bytes / (key_size + load_value_size)))
	"$(dirname $0)"/dbbench-load-L2.sh "$output_dir" "$num_unique_keys" "$key_size" "$load_value_size" || exit $?
	"$(dirname $0)"/dbbench-$version-run.sh "$output_dir" "$num_unique_keys" "$key_size" \
		--benchmarks=$benchmark,stats \
		--value_size="$load_value_size" \
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
		--value_size="$load_value_size" \
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
with_rate_limiter_auto_tuned() (
	suffix="-autotuned$suffix" "$@" \
		--rate_limiter_auto_tuned=true
)

mixgraph_wo() (
	version=$1
	shift
	threads=$1
	shift
	sine_a=100000
	sine_b=0.02
	sine_d=150000
	key_size=48
	load_value_size=43
	num_unique_keys=$((unique_bytes / (key_size + load_value_size)))
	num_overwrites=4
	# --reads is actually the number of all operations for mixgraph
	test_three_levels "mixgraph-wo-num-overwrites-$num_overwrites-cache-1GB-sine_a-$sine_a-sine_b-$sine_b-sine_d-$sine_d-threads-$threads$suffix" \
		"$version" mixgraph "$key_size" "$load_value_size" "$@" \
			--reads=$(($num_overwrites * num_unique_keys / threads)) \
			--threads="$threads" \
			--cache_size=1000000000 \
			--sine_a=$sine_a \
			--sine_b=$sine_b \
			--sine_d=$sine_d \
			--mix_get_ratio=0 \
			--mix_put_ratio=1 \
			--mix_seek_ratio=0 \
			--keyrange_dist_a=14.18 \
			--keyrange_dist_b=-2.917 \
			--keyrange_dist_c=0.0164 \
			--keyrange_dist_d=-0.08082 \
			--keyrange_num=30 \
			--value_k=0.2615 \
			--value_sigma=25.45 \
			--iter_k=2.517 \
			--iter_sigma=14.236 \
			--sine_mix_rate_interval_milliseconds=5000 \
			--sine_mix_rate=true
)
with_compaction_limit_MB_s 100 mixgraph_wo dynamic-tiering 16
with_compaction_limit_MB_s 100 mixgraph_wo dynamic-size-ratio 16

meituan() (
	workspace=$(realpath "$(dirname $0)"/../..)
	version=$1
	shift
	threads=$1
	shift
	key_size=16
	value_size=200
	speedup=100
	period_secs=144
	repeat=10
	writes_per_second_file=$(mktemp)
	reads_per_second_file=$(mktemp)
	command="rm $writes_per_second_file $reads_per_second_file"
	trap "echo $command; $command" EXIT
	awk "{print \$0 * $speedup}" "$workspace"/meituan/write.txt > $writes_per_second_file
	awk "{print \$0 * $speedup}" "$workspace"/meituan/read.txt > $reads_per_second_file
	test_three_levels "meituan-speedup-$speedup-period-secs-$period_secs-repeat-$repeat-value-size-$value_size-threads-$threads$suffix" \
		"$version" "customperiodic" "$key_size" "$value_size" "$@" \
			--threads="$threads" \
			--period_secs="$period_secs" \
			--writes_per_second_file="$writes_per_second_file" \
			--reads_per_second_file="$reads_per_second_file" \
			--duration=$((period_secs * repeat))
)
with_compaction_limit_MB_s 100 meituan dynamic-size-ratio 16

read=10000
while [ "$read" -le 70000 ]; do
	suffix="-threads-16-read-$read" with_bgwrite_MB_s 10 test_rocksdb leveling queuedreadrandomwhilewriting 24 1000 --threads=16 --benchmark_read_rate_limit=$read
	suffix="-threads-16-read-$read" with_bgwrite_MB_s 10 with_compaction_limit_MB_s 100 test_rocksdb leveling queuedreadrandomwhilewriting 24 1000 --threads=16 --benchmark_read_rate_limit=$read
	read=$((read + 10000))
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
