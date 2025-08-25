#!/usr/bin/env sh

../helper/build.sh

with_memtable_size() (
	arg_memtable_size=$1
	shift
	memtable_size=$(humanfriendly --parse-size="$arg_memtable_size")
	suffix="-memtable-$arg_memtable_size$suffix" "$@" \
		--write_buffer_size=$memtable_size \
		--target_file_size_base=$memtable_size \
		--max_bytes_for_level_base=$((memtable_size * 4))
)

with_policy_leveling() {
	T=$1
	shift
	"$@" \
		--level_compaction_dynamic_level_bytes=true \
		--max_bytes_for_level_multiplier=$T \
		--num_levels=10
}
with_policy_universal() {
	"$@" \
		--compaction_style=1 \
		--num_levels=1
}
with_policy_tiering() (
	T=$1
	shift
	"$@" \
		--compaction_style=4 \
		--compaction_policy="tiering" \
		--max_bytes_for_level_multiplier=$T \
		--num_levels=1 \
		--max_background_jobs=100
)
with_policy_benefit_cost() {
	"$@" \
		--compaction_style=6 \
		--num_levels=1
}

with_writes_per_writer() {
	writes_per_thread=$1
	shift
	"$@" --writes="$writes_per_thread" --finish_after_writes=true
}
with_write_MB_s() (
	write_MB_s=$1
	shift
	suffix="-write-${write_MB_s}MB-s$suffix" "$@" \
		--benchmark_write_rate_limit=$((write_MB_s * 1000000))
)
with_read_ops() (
	read_ops=$1
	shift
	suffix="-read-ops-$read_ops$suffix" "$@" \
		--benchmark_read_rate_limit="$read_ops"
)

with_threads() (
	threads=$1
	shift
	suffix="-threads-$threads$suffix" "$@" \
		--threads="$threads"
)
with_cache() (
	cache=$1
	shift
	cache_size=$(humanfriendly --parse-size="$cache")
	suffix="-cache-$cache$suffix" "$@" \
		--cache_size="$cache_size"
)
with_exp_range() (
	exp_range=$1
	shift
	suffix="-exp-range-$exp_range$suffix" "$@" \
		--read_random_exp_range="$exp_range"
)

dbbench() (
	output_dir=$1
	shift
	benchmark=$1
	shift
	key_size=$1
	shift
	value_size=$1
	shift
	unique_size=$1
	shift
	num_unique_keys=$(($(humanfriendly --parse-size="$unique_size") / (key_size + value_size)))
	"$(dirname $0)"/prepare.sh "$output_dir" || return $?
	"$(dirname $0)"/dbbench.sh "$output_dir" "$num_unique_keys" "$key_size" \
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
	key_size=$1
	shift
	value_size=$1
	shift
	unique_size=$1
	shift
	output_dir="../../data/$benchmark-unique-size-$unique_size$suffix/$version"
	dbbench "$output_dir" "$benchmark" "$key_size" "$value_size" "$unique_size" "$@"
)

with_compaction_limit_MB_s() (
	compaction_MB_s=$1
	shift
	suffix="-compaction-${compaction_MB_s}MB-s$suffix" "$@" \
		--rate_limiter_bytes_per_sec=$(($compaction_MB_s * 1000000))
)
with_rate_limiter_auto_tuned() (
	suffix="-rate-limiter-autotuned$suffix" "$@" \
		--rate_limiter_bytes_per_sec=1000000000 \
		--rate_limiter_auto_tuned=true
)

with_max_running_background_jobs() (
	max_running_bg_jobs=$1
	shift
	suffix="-max-running-bg-jobs-$max_running_bg_jobs$suffix" "$@" \
		--max_background_jobs=100 \
		--max_running_background_jobs=$max_running_bg_jobs
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
	workload_name="mixgraph-wo-writes-$writes-sine_a-$sine_a-sine_b-$sine_b-sine_d-$sine_d-threads-$threads$suffix"
	output_dir=../../data/$workload_name/$version
	# --reads is actually the number of all operations for mixgraph
	dbbench "$output_dir" \
		mixgraph "$key_size" "$load_value_size" \
			--reads=$(($writes / threads)) \
			--threads="$threads" \
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
	speedup=$1
	shift
	scale=$1
	shift
	unique_size=$1
	shift
	key_size=16
	value_size=1000
	repeat=8
	period_secs=$((24 * 3600 / speedup))
	writes_per_second_file=$(mktemp)
	reads_per_second_file=$(mktemp)
	command="rm $writes_per_second_file $reads_per_second_file"
	trap "echo $command; $command" EXIT
	awk "{print \$0 * $speedup * $scale}" "$workspace"/meituan/write.txt > $writes_per_second_file
	awk "{print \$0 * $speedup * $scale}" "$workspace"/meituan/read.txt > $reads_per_second_file
	workload_name="meituan-speedup-$speedup-scale-$scale-repeat-$repeat-value-size-$value_size-unique-size-$unique_size$suffix"
	output_dir=../../data/$workload_name/$version
	dbbench "$output_dir" "customperiodic" "$key_size" "$value_size" "$unique_size" \
		--period_secs="$period_secs" \
		--writes_per_second_file="$writes_per_second_file" \
		--reads_per_second_file="$reads_per_second_file" \
		--duration=$((period_secs * repeat)) \
		"$@"
)
threads=32
cache=100MB
exp_range=16
speedup=50
with_threads $threads with_exp_range $exp_range with_cache $cache with_memtable_size 8MB with_policy_leveling 3 meituan leveling3 $speedup 1 10GB
with_threads $threads with_exp_range $exp_range with_cache $cache with_memtable_size 8MB with_policy_tiering 2 meituan tiering2 $speedup 1 10GB
with_threads $threads with_exp_range $exp_range with_cache $cache with_memtable_size 8MB with_policy_universal meituan universal $speedup 1 10GB
with_threads $threads with_exp_range $exp_range with_cache $cache with_memtable_size 8MB with_policy_benefit_cost meituan benefit-cost $speedup 1 10GB
with_threads $threads with_exp_range $exp_range with_cache $cache with_memtable_size 8MB with_rate_limiter_auto_tuned with_policy_benefit_cost meituan benefit-cost $speedup 1 10GB

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
