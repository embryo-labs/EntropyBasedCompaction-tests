#!/usr/bin/env sh
. $(dirname $0)/common.sh

../helper/build.sh

with_policy_leveling() {
	T=$1
	shift
	"$@" \
		--level_compaction_dynamic_level_bytes=true \
		--max_bytes_for_level_base=$((memtable_size * 4)) \
		--max_bytes_for_level_multiplier=$T \
		--num_levels=10
}
with_policy_universal() {
	"$@" \
		--compaction_style=1 \
		--num_levels=1
}
with_policy_tiering() {
	T=$1
	shift
	"$@" \
		--compaction_style=4 \
		--compaction_policy="tiering" \
		--max_bytes_for_level_multiplier=$T \
		--num_levels=1
}
with_policy_benefit_cost() {
	"$@" \
		--compaction_style=6 \
		--num_levels=1
}

run_rocksdb() (
	output_dir=$1
	shift
	benchmark=$1
	shift
	key_size=$1
	shift
	value_size=$1
	shift
	num_unique_keys=$((unique_bytes / (key_size + value_size)))
	"$(dirname $0)"/dbbench-run.sh "$output_dir" "$num_unique_keys" "$key_size" \
		--benchmarks=$benchmark,stats \
		--value_size="$value_size" \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)

test_rocksdb() (
	version=$1
	shift
	benchmark=$1
	shift
	output_dir="../../data/$benchmark$suffix/$version"
	"$(dirname $0)"/prepare.sh "$output_dir" || return $?
	run_rocksdb "$output_dir" "$benchmark" "$@"
	mkdir "$output_dir"/load
	mv "$output_dir"/* "$output_dir"/load
	run_rocksdb "$output_dir" "$benchmark" "$@"
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
	sine_b=0.1
	sine_d=101000
	key_size=48
	load_value_size=43
	num_unique_keys=$((unique_bytes / (key_size + load_value_size)))
	writes=100000000
	workload_name="mixgraph-wo-writes-$writes-cache-1GB-sine_a-$sine_a-sine_b-$sine_b-sine_d-$sine_d-threads-$threads$suffix"
	output_dir=../../data/$workload_name/$version
	"$(dirname $0)"/prepare.sh "$output_dir" || return $?
	# --reads is actually the number of all operations for mixgraph
	run_rocksdb "$output_dir" \
		mixgraph "$key_size" "$load_value_size" \
			--reads=$(($writes / threads)) \
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
			--sine_mix_rate=true \
			"$@"
)
with_compaction_limit_MB_s 100 with_policy_leveling 3 mixgraph_wo leveling3 16
with_compaction_limit_MB_s 100 with_policy_tiering 2 mixgraph_wo tiering2 16
with_compaction_limit_MB_s 100 with_policy_universal mixgraph_wo universal 16
with_compaction_limit_MB_s 100 with_policy_benefit_cost mixgraph_wo benefit-cost 16

meituan() (
	workspace=$(realpath "$(dirname $0)"/../..)
	version=$1
	shift
	period_secs=$1
	shift
	speedup=$1
	shift
	threads=$1
	shift
	key_size=16
	value_size=1000
	repeat=10
	writes_per_second_file=$(mktemp)
	reads_per_second_file=$(mktemp)
	compaction_limit_file=$(mktemp)
	command="rm $writes_per_second_file $reads_per_second_file"
	trap "echo $command; $command" EXIT
	awk "{print \$0 * $speedup}" "$workspace"/meituan/write.txt > $writes_per_second_file
	awk "{print \$0 * $speedup}" "$workspace"/meituan/read.txt > $reads_per_second_file
	awk "{print \$0 * 1000000}" $workspace/meituan/compaction-MB-s.txt > $compaction_limit_file
	workload_name="meituan-speedup-$speedup-period-secs-$period_secs-repeat-$repeat-value-size-$value_size-threads-$threads$suffix"
	output_dir=../../data/$workload_name/$version
	"$(dirname $0)"/prepare.sh "$output_dir" || return $?
	run_rocksdb "$output_dir" "customperiodic" "$key_size" "$value_size" \
		--threads="$threads" \
		--period_secs="$period_secs" \
		--writes_per_second_file="$writes_per_second_file" \
		--reads_per_second_file="$reads_per_second_file" \
		--compaction_limit_file="$compaction_limit_file" \
		--duration=$((period_secs * repeat)) \
		"$@"
)
with_policy_leveling 3 meituan leveling3 144 10 128
with_policy_tiering 2 meituan tiering2 144 10 128
with_policy_universal meituan universal 144 10 128
with_policy_benefit_cost meituan benefit-cost 144 10 128

read=10000
while [ "$read" -le 70000 ]; do
	suffix="-threads-16-read-$read" with_bgwrite_MB_s 10 with_policy_leveling 3 test_rocksdb leveling3 queuedreadrandomwhilewriting 24 1000 --threads=16 --benchmark_read_rate_limit=$read
	suffix="-threads-16-read-$read" with_bgwrite_MB_s 10 with_compaction_limit_MB_s 100 with_policy_leveling 3 test_rocksdb leveling3 queuedreadrandomwhilewriting 24 1000 --threads=16 --benchmark_read_rate_limit=$read
	read=$((read + 10000))
done

bench=seekrandomwhilewriting
suffix="-threads-16"
args="--threads=16"

write=1
while [ "$write" -le 20 ]; do
	suffix="$suffix" with_bgwrite_MB_s $write with_compaction_limit_MB_s 100 with_policy_leveling 3 test_rocksdb leveling3 "$bench" 24 1000 $args
	suffix="$suffix" with_bgwrite_MB_s $write with_compaction_limit_MB_s 100 with_policy_universal test_rocksdb universal "$bench" 24 1000 $args
	write=$((write + 1))
done
