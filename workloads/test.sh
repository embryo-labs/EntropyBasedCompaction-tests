#!/usr/bin/env sh
workspace=$(realpath "$(dirname $0)"/../..)
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
		--max_bytes_for_level_multiplier=5 \
		--level0_file_num_compaction_trigger=1
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
		--compaction_style=3 \
		--max_bytes_for_level_multiplier=$T \
		--num_levels=1 \
		--max_background_jobs=100
)
with_policy_benefit_cost() {
	"$@" \
		--compaction_style=5 \
		--num_levels=1
}
with_policy_no_sliding_window() {
	"$@" \
		--compaction_style=5 \
		--num_levels=1 \
		--sliding_window=false
}
with_policy_preempt_only_by_entropy() (
	k_e=$1
	shift
	"$@" \
		--compaction_style=5 \
		--num_levels=1 \
		--sliding_window=false \
		--preempt_by_entropy=true \
		--preempt_by_num=false \
		--k_e="$k_e"
)
with_policy_preempt_only_by_num() {
	"$@" \
		--compaction_style=5 \
		--num_levels=1 \
		--sliding_window=false \
		--preempt_by_entropy=false \
		--preempt_by_num=true
}

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
	# We specify large readahead_size so that data in the range can be prefetched in one I/O.
	# Out-of-range part will not be prefetched due to auto_readahead_size.
	suffix="-nexts-$nexts$suffix" "$@" \
		--seek_nexts="$nexts" \
		--max_scan_distance="$nexts" \
		--readahead_size=$((1024 * 1024))
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

with_meituan_scan_len() {
	suffix="-scan-len-meituan$suffix" "$@" --scan_length_cdf_file="$workspace/meituan/scan-length.txt"
}
with_meituan_read() (
	get_ratio=0.87
	seek_ratio=0.13
	suffix="-get-$get_ratio-seek-$seek_ratio$suffix" \
		with_meituan_scan_len "$@" \
			--mix_get_ratio=$get_ratio \
			--mix_seek_ratio=$seek_ratio
)
seek_only() {
	suffix="-seek-1$suffix" "$@" --mix_get_ratio=0 --mix_seek_ratio=1
}

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
		\"name\": \"overwrite\",
		\"threads\": 1,
		\"duration\": 0,
		\"writes\": $((num_unique_keys / 10)),
		\"benchmark_write_rate_limit\": 10000000
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

key_size=16
value_size=1000
write=100GB
writes=$(($(humanfriendly --parse-size="$write") / (key_size + value_size)))
compaction_MB_s=200
for write_MB_s in 10 20 30 40 50 60; do
	read_workload() {
		seek_only with_nexts $nexts "$@"
	}
	suffix="-write-$write" read_workload with_writes_per_writer "$writes" with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_rocksdb_tuned dbbench_load_all rocksdb-tuned readwhilewriting $key_size $value_size 10GB
	suffix="-write-$write" read_workload with_writes_per_writer "$writes" with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_universal dbbench_load_all universal readwhilewriting $key_size $value_size 10GB

	for ratio in 2 4 8; do
		suffix="-write-$write" read_workload with_writes_per_writer "$writes" with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_tiering $ratio dbbench_load_all tiering$ratio readwhilewriting $key_size $value_size 10GB
	done
	suffix="-write-$write" read_workload with_writes_per_writer "$writes" with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_benefit_cost dbbench_load_all benefit-cost readwhilewriting $key_size $value_size 10GB

	suffix="-write-$write" read_workload with_writes_per_writer "$writes" with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_preempt_only_by_entropy 1 dbbench_load_all preempt-only-by-entropy-ke-1 readwhilewriting $key_size $value_size 10GB
	suffix="-write-$write" read_workload with_writes_per_writer "$writes" with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_preempt_only_by_num dbbench_load_all preempt-only-by-num readwhilewriting $key_size $value_size 10GB
	suffix="-write-$write" read_workload with_writes_per_writer "$writes" with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_no_sliding_window dbbench_load_all no-sliding-window readwhilewriting $key_size $value_size 10GB
done

meituan_writer() (
	workspace=$(realpath "$(dirname $0)"/../..)
	version=$1
	shift
	period_secs=$1
	shift
	speedup=$1
	shift
	unique_size=$1
	shift
	key_size=16
	value_size=503
	repeat=1
	writes_per_second_file=$(mktemp)
	command="rm $writes_per_second_file"
	trap "echo $command; $command" EXIT
	awk "{print \$0 * $speedup}" "$workspace"/meituan/write.txt > $writes_per_second_file
	workload_name="meituan-writer-period-secs-$period_secs-speedup-$speedup-repeat-$repeat-key-$key_size-value-$value_size-unique-size-$unique_size$suffix"
	output_dir=../../data/$workload_name/$version
	load_all_run "$output_dir" "customperiodic" "$key_size" "$value_size" "$unique_size" \
		--period_secs="$period_secs" \
		--writes_per_second_file="$writes_per_second_file" \
		--scan_length_cdf_file="$workspace/meituan/scan-length.txt" \
		--duration=$((period_secs * repeat)) \
		"$@"
)
period_secs=$((3600 * 4))
speedup=24
get_ratio=0.87
seek_ratio=0.13

compaction_MB_s=200
suffix="-get-$get_ratio-seek-$seek_ratio" with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_leveling 5 meituan_writer leveling5 $period_secs $speedup 10GB --mix_get_ratio=$get_ratio --mix_seek_ratio=$seek_ratio
suffix="-get-$get_ratio-seek-$seek_ratio" with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_rocksdb_tuned meituan_writer rocksdb-tuned $period_secs $speedup 10GB --mix_get_ratio=$get_ratio --mix_seek_ratio=$seek_ratio
suffix="-get-$get_ratio-seek-$seek_ratio" with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_universal meituan_writer universal $period_secs $speedup 10GB --mix_get_ratio=$get_ratio --mix_seek_ratio=$seek_ratio

for ratio in 2 4 8; do
	suffix="-get-$get_ratio-seek-$seek_ratio" with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_tiering $ratio meituan_writer tiering$ratio $period_secs $speedup 10GB --mix_get_ratio=$get_ratio --mix_seek_ratio=$seek_ratio
done
suffix="-get-$get_ratio-seek-$seek_ratio" with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_benefit_cost meituan_writer benefit-cost $period_secs $speedup 10GB --mix_get_ratio=$get_ratio --mix_seek_ratio=$seek_ratio
