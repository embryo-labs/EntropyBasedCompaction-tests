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

with_policy_rocksdb_tuned() (
	"$@" \
		--level_compaction_dynamic_level_bytes=true \
		--num_levels=10 \
		--max_bytes_for_level_multiplier=10
)
with_policy_leveling() (
	T=$1
	shift
	"$@" \
		--level_compaction_dynamic_level_bytes=true \
		--num_levels=10 \
		--max_bytes_for_level_multiplier=$T \
		--level0_file_num_compaction_trigger=1 \
		--allow_intra_l0_compactions=false
)
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

with_num_writers() (
	num_writers=$1
	shift
	suffix="-writers-$num_writers$suffix" "$@" \
		--num_writers=$num_writers
)
with_writes_per_writer() {
	writes_per_thread=$1
	shift
	"$@" --writes="$writes_per_thread" --finish_after_writes=true
}
with_write_MB_s() (
	write_MB_s=$1
	shift
	per_writer=$((write_MB_s * 1000000))
	if [ "$num_writers" ]; then
		per_writer=$((per_writer / num_writers))
		echo "$per_writer" B/s per writer
	fi
	suffix="-write-${write_MB_s}MB-s$suffix" "$@" \
		--benchmark_write_rate_limit=$per_writer
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
with_read_exp_range() (
	exp_range=$1
	shift
	suffix="-exp-range-$exp_range$suffix" "$@" \
		--read_random_exp_range="$exp_range"
)
with_write_exp_range() (
	exp_range=$1
	shift
	suffix="-write-exp-range-$exp_range$suffix" "$@" \
		--write_random_exp_range="$exp_range"
)
with_nexts() (
	nexts=$1
	shift
	suffix="-nexts-$nexts$suffix" "$@" --seek_nexts="$nexts"
)
with_merge_operator() (
	op=$1
	shift
	suffix="-merge-operator-$op$suffix" "$@" \
		--merge_operator="$op"
)
with_perf_level() (
	perf_level=$1
	shift
	suffix="-perf-level-$perf_level$suffix" "$@" \
		--perf_level=$perf_level
)

load_some_run() (
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
	load_size=$1
	shift
	num_unique_keys=$(($(humanfriendly --parse-size="$unique_size") / (key_size + value_size)))
	num_load_keys=$(($(humanfriendly --parse-size="$load_size") / (key_size + value_size)))
	"$(dirname $0)"/prepare.sh "$output_dir" || return $?
	"$(dirname $0)"/dbbench.sh "$output_dir" "$num_unique_keys" "$key_size" \
		--value_size="$value_size" \
		--benchmarks_json="[
	{
		\"name\": \"fillrandom\",
		\"threads\": 1,
		\"duration\": 0,
		\"writes\": $num_load_keys,
		\"benchmark_write_rate_limit\": 0
	},
	{
		\"name\": \"waitforcompaction\"
	},
	{
		\"name\": \"stats\"
	},
	{
		\"name\": \"$benchmark\"
	},
	{
		\"name\": \"stats\"
	}
]" "$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)
load_all_run() (
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
		--value_size="$value_size" \
		--benchmarks_json="[
	{
		\"name\": \"filluniquerandom\",
		\"threads\": 1,
		\"duration\": 0,
		\"writes\": $num_unique_keys,
		\"benchmark_write_rate_limit\": 0
	},
	{
		\"name\": \"waitforcompaction\"
	},
	{
		\"name\": \"stats\"
	},
	{
		\"name\": \"resetstats\"
	},
	{
		\"name\": \"$benchmark\"
	},
	{
		\"name\": \"stats\"
	}
]" "$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)

dbbench_load_some() (
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
	load_size=$1
	shift
	output_dir="../../data/$benchmark-key-$key_size-value-$value_size-unique-size-$unique_size-load-$load_size$suffix/$version"
	load_some_run "$output_dir" "$benchmark" "$key_size" "$value_size" "$unique_size" "$load_size" "$@"
)
dbbench_load_all() (
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
	output_dir="../../data/$benchmark-key-$key_size-value-$value_size-unique-size-$unique_size$suffix/$version"
	load_all_run "$output_dir" "$benchmark" "$key_size" "$value_size" "$unique_size" "$@"
)

with_compaction_limit_MB_s() (
	compaction_MB_s=$1
	shift
	suffix="-compaction-${compaction_MB_s}MB-s$suffix" "$@" \
		--rate_limiter_bytes_per_sec=$(($compaction_MB_s * 1000000))
)

with_max_running_background_jobs() (
	max_running_bg_jobs=$1
	shift
	suffix="-max-running-bg-jobs-$max_running_bg_jobs$suffix" "$@" \
		--max_background_jobs=100 \
		--max_running_background_jobs=$max_running_bg_jobs
)


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
	load_all_run "$output_dir" "customperiodic" "$key_size" "$value_size" "$unique_size" \
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
with_threads $threads with_read_exp_range $exp_range with_cache $cache with_memtable_size 8MiB with_policy_leveling 3 meituan leveling3 $speedup 1 10GB
with_threads $threads with_read_exp_range $exp_range with_cache $cache with_memtable_size 8MiB with_policy_tiering 2 meituan tiering2 $speedup 1 10GB
with_threads $threads with_read_exp_range $exp_range with_cache $cache with_memtable_size 8MiB with_policy_universal meituan universal $speedup 1 10GB
with_threads $threads with_read_exp_range $exp_range with_cache $cache with_memtable_size 8MiB with_policy_benefit_cost meituan benefit-cost $speedup 1 10GB
