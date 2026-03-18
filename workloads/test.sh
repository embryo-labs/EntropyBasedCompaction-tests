#!/usr/bin/env sh
workspace=$(realpath "$(dirname $0)"/../..)
nice ../helper/build.sh

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
with_policy_entropy_based() {
	"$@" \
		--compaction_style=7 \
		--num_levels=1
}
with_policy_entropy_based_universal() {
	with_policy_entropy_based "$@" \
		--pick_candidates_with_universal=true
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
with_entropy_threshold() (
	entropy_threshold=$1
	shift
	suffix="-entropy-threshold-$entropy_threshold$suffix" "$@" \
		--entropy_threshold=$entropy_threshold
)
with_k_n() (
	k_n=$1
	shift
	suffix="-k_n-$k_n$suffix" "$@" --k_n=$k_n
)

no_exclude_small() {
	"$@" \
		--exclude_small_sorted_runs=false
}
no_preemption_conditions() {
	"$@" \
		--preempt_by_entropy=false \
		--preempt_by_num=false
}
preempt_only_by_entropy() (
	b_e=$1
	shift
	"$@" \
		--preempt_by_entropy=true \
		--preempt_by_num=false \
		--b_e="$b_e"
)
preempt_only_by_num() {
	"$@" \
		--preempt_by_entropy=false \
		--preempt_by_num=true
}

with_compaction_trigger() {
	compaction_trigger=$1
	shift
	suffix="-compaction-trigger-$compaction_trigger$suffix" "$@" \
		--level0_file_num_compaction_trigger=$compaction_trigger
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

with_meituan_ratio() (
	get_ratio=0.87
	seek_ratio=0.13
	suffix="-get-$get_ratio-seek-$seek_ratio$suffix" "$@" \
		--mix_get_ratio=$get_ratio \
		--mix_seek_ratio=$seek_ratio
)
seek_only() {
	suffix="-seek-1$suffix" "$@" --mix_get_ratio=0 --mix_seek_ratio=1
}

with_compaction_limit_MB_s() (
	compaction_MB_s=$1
	shift
	suffix="-compaction-${compaction_MB_s}MB-s$suffix" "$@" \
		--rate_limiter_bytes_per_sec=$((compaction_MB_s * 1000000))
)
with_io_sa_limit_MB_s() (
	io_sa_limit_MB_s=$1
	shift
	suffix="-io_sa-${io_sa_limit_MB_s}MB-s$suffix" "$@" \
		--rate_limiter_bytes_per_sec_io_sa=$((io_sa_limit_MB_s * 1000000)) \
		--last_compaction_io_sa=true
)

with_max_running_background_jobs() (
	max_running_bg_jobs=$1
	shift
	suffix="-max-running-bg-jobs-$max_running_bg_jobs$suffix" "$@" \
		--max_background_jobs=100 \
		--max_running_background_jobs=$max_running_bg_jobs
)

load_all_warmup_run() (
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
	warmup_secs=$1
	shift
	run_secs=$1
	shift
	output_dir="../../data/$benchmark-key-$key_size-value-$value_size-unique-size-$unique_size-warmup-secs-$warmup_secs-run-secs-$run_secs$suffix/$version"
	num_unique_keys=$(($(humanfriendly --parse-size="$unique_size") / (key_size + value_size)))

	"$(dirname $0)"/prepare.sh "$output_dir" || return $?
	mkdir -p "$output_dir"/load
	mkdir -p "$output_dir"/warmup
	"$(dirname $0)"/dbbench.sh "$output_dir" "$num_unique_keys" "$key_size" \
		--value_size="$value_size" \
		--benchmarks_json="[
	{
		\"output_dir\": \"load\",
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
		\"output_dir\": \"warmup\",
		\"name\": \"$benchmark\",
		\"duration\": $warmup_secs
	},
	{
		\"name\": \"stats\"
	},
	{
		\"name\": \"resetstats\"
	},
	{
		\"name\": \"$benchmark\",
		\"duration\": $run_secs
	},
	{
		\"name\": \"stats\"
	}
]" "$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)

key_size=16
value_size=603
unique_size=10GB
warmup_secs=1200
run_secs=1200
compaction_MB_s=200
read_workload() {
	with_nexts 48 with_meituan_ratio "$@"
}
for write_MB_s in 10 30 50; do
	read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_rocksdb_tuned load_all_warmup_run rocksdb-tuned readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_universal load_all_warmup_run universal readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs

	for ratio in 2 4 8; do
		read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_tiering $ratio load_all_warmup_run tiering$ratio readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	done
done

for write_MB_s in 10 20 30 40 50 60; do
	# Soft preemption
	read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_compaction_trigger 2 with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs

	# Strict preemption

	read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_compaction_trigger 2 with_entropy_threshold "$(python3 -c "import math; print(math.log2(math.e * 1250) / ($compaction_MB_s / $write_MB_s - 1))")" with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_compaction_trigger 2 with_policy_entropy_based preempt_only_by_entropy 0 load_all_warmup_run preempt_only_by_entropy-be-0 readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_compaction_trigger 2 with_policy_entropy_based preempt_only_by_num load_all_warmup_run preempt_only_by_num readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_compaction_trigger 2 with_policy_entropy_based no_exclude_small load_all_warmup_run no_exclude_small readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs

	read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_compaction_trigger 2 with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done

for t_e in 0 1 2 3 4 5 6; do
	read_workload with_write_MB_s 10 with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_compaction_trigger 2 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 0 0.5 0.9 1 2 3 4 5 6; do
	read_workload with_write_MB_s 20 with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_compaction_trigger 2 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 0 1 1.5 1.6 2 2.5 3 4 5 6; do
	read_workload with_write_MB_s 30 with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_compaction_trigger 2 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 0 1 1.5 2 2.3 2.5 2.8 3 3.5 4 5 6; do
	read_workload with_write_MB_s 40 with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_compaction_trigger 2 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 2.5 3 3.1 3.2 3.5 4 5 6; do
	read_workload with_write_MB_s 50 with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_compaction_trigger 2 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 3.7 3.8 3.9 4 4.5 5 5.5 6; do
	read_workload with_write_MB_s 60 with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_compaction_trigger 2 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done

for t_e in 0 0.5 1 2 3; do
	for write_MB_s in 10 20 30 40 50 60; do
		read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_entropy_threshold $t_e with_policy_benefit_cost load_all_warmup_run benefit-cost readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	done
done

for k_n in 1.4 2 4 8 16 32 64; do
	for write_MB_s in 10 50; do
		read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_k_n $k_n with_policy_benefit_cost load_all_warmup_run benefit-cost readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	done
done

for io_sa in 10 30 50 70 90; do
	for write_MB_s in 30 50; do
		read_workload with_write_MB_s $write_MB_s with_compaction_limit_MB_s $compaction_MB_s with_io_sa_limit_MB_s $io_sa with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_benefit_cost load_all_warmup_run benefit-cost readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	done
done

meituan_writer() (
	workspace=$(realpath "$(dirname $0)"/../..)
	version=$1
	shift
	type=$1
	shift
	period_secs=$1
	shift
	num_shards=$1
	shift
	unique_size=$1
	shift
	key_size=16
	value_size=603
	writes_per_second_file=$(mktemp)
	command="rm $writes_per_second_file"
	trap "echo $command; $command" EXIT
	echo $writes_per_second_file
	awk "{print \$0 / $num_shards}" "$workspace/tests/meituan/write-speed-$type-day" > $writes_per_second_file
	workload_name="meituan-writer-$type-day-period-secs-$period_secs-num_shards-$num_shards-key-$key_size-value-$value_size-unique-size-$unique_size$suffix"
	output_dir=../../data/$workload_name/$version

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
		\"name\": \"customperiodic\"
	},
	{
		\"name\": \"stats\"
	}
]" \
		--period_secs="$period_secs" \
		--writes_per_second_file="$writes_per_second_file" \
		--duration=$period_secs \
		"$@"
	"$(dirname $0)"/../helper/data-rocksdb.sh "$output_dir"
	"$(dirname $0)"/../helper/plot-rocksdb.sh "$output_dir"
)
unique_size=10GB
period_secs=$((3600 * 3))
num_shards=5
compaction_MB_s=200
read_workload() {
	with_nexts 48 with_meituan_ratio "$@"
}
for type in peak normal; do
	read_workload with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_rocksdb_tuned meituan_writer rocksdb-tuned $type $period_secs $num_shards $unique_size
	read_workload with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB with_policy_universal meituan_writer universal $type $period_secs $num_shards $unique_size

	for ratio in 2 4 8; do
		read_workload with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_tiering $ratio meituan_writer tiering$ratio $type $period_secs $num_shards $unique_size
	done
	read_workload with_compaction_limit_MB_s $compaction_MB_s with_max_running_background_jobs 1 with_memtable_size 8MiB with_policy_benefit_cost meituan_writer benefit-cost $type $period_secs $num_shards $unique_size
done
