with_policy_rocksdb_tuned() (
	db_bench_path="$workspace"/rocksdb/build/db_bench "$@" \
		--level_compaction_dynamic_level_bytes=true \
		--num_levels=10 \
		--max_background_jobs=16 \
		--max_bytes_for_level_multiplier=5 \
		--level0_file_num_compaction_trigger=1
)
with_policy_leveling() (
	T=$1
	shift
	db_bench_path="$workspace"/rocksdb/build/db_bench "$@" \
		--level_compaction_dynamic_level_bytes=true \
		--num_levels=10 \
		--max_background_jobs=16 \
		--max_bytes_for_level_multiplier=$T \
		--level0_file_num_compaction_trigger=1 \
		--allow_intra_l0_compactions=false
)
with_policy_universal_hard_trigger() {
	db_bench_path="$workspace"/rocksdb/build/db_bench "$@" \
		--compaction_style=1 \
		--num_levels=1 \
		--max_background_jobs=16
}
with_policy_entropy_based() {
	db_bench_path="$workspace"/rocksdb/build/db_bench "$@" \
		--compaction_style=3 \
		--num_levels=1 \
		--max_background_jobs=16 \
		--level0_file_num_compaction_trigger=2 \
		--json_log_file="$workspace/testdb/log.json"
}
with_policy_entropy_based_universal() {
	with_policy_entropy_based "$@" \
		--pick_candidates_with_universal=true
}
with_policy_tiering() (
	T=$1
	shift
	db_bench_path="$workspace"/rocksdb/build/db_bench "$@" \
		--compaction_style=4 \
		--max_bytes_for_level_multiplier=$T \
		--num_levels=1 \
		--max_background_jobs=100
)
with_policy_lazy_leveling() (
	T=$1
	shift
	C=$1
	shift
	db_bench_path="$workspace"/rocksdb/build/db_bench "$@" \
		--compaction_style=5 \
		--num_levels=1 \
		--max_bytes_for_level_multiplier=$T \
		--C=$C \
		--max_background_jobs=100
)
with_policy_bush() (
	db_bench_path="$workspace"/rocksdb/build/db_bench "$@" \
		--compaction_style=6 \
		--num_levels=1 \
		--num_logical_levels=4 \
		--max_background_jobs=100
)
with_policy_vertiorizon() (
	num_horizontal_levels=$1
	shift
	k=$1
	shift
	db_bench_path="$workspace"/rocksdb/build/db_bench "$@" \
		--compaction_style=7 \
		--num_levels=3 \
		--num_horizontal_levels=$num_horizontal_levels \
		--k=$k \
		--max_background_jobs=100
)

with_entropy_threshold() (
	entropy_threshold=$1
	shift
	suffix="-entropy-threshold-$entropy_threshold$suffix" "$@" \
		--entropy_threshold=$entropy_threshold
)
autotune_entropy_threshold() {
	suffix="-autotune_entropy_threshold$suffix" "$@" \
		--autotune_entropy_threshold=true
}
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
		--preempt_by_num=true \
		--pick_best_reff=false
}

with_memtable_size() (
	arg_memtable_size=$1
	shift
	memtable_size=$(humanfriendly --parse-size="$arg_memtable_size")
	suffix="-memtable-$arg_memtable_size$suffix" "$@" \
		--write_buffer_size=$memtable_size \
		--target_file_size_base=$memtable_size \
		--max_bytes_for_level_base=$((memtable_size * 4))
)
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
with_stall_trigger() (
	slowdown=$1
	shift
	stop=$1
	shift
	suffix="-slowdown-$slowdown-stop-$stop$suffix" "$@" \
		--level0_slowdown_writes_trigger=$slowdown \
		--level0_stop_writes_trigger=$stop
)
no_stall() {
	suffix="-no-stall$suffix" "$@" \
		--level0_slowdown_writes_trigger=100000 \
		--level0_stop_writes_trigger=100000
}

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
with_write_zipfian_theta() (
	zipfian_theta=$1
	shift
	suffix="-write_zipfian_theta-$zipfian_theta$suffix" "$@" \
		--write_zipfian_theta="$zipfian_theta"
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
	output_dir="$workspace/data/$benchmark-key-$key_size-value-$value_size-unique-size-$unique_size-warmup-secs-$warmup_secs-run-secs-$run_secs$suffix/$version"
	num_unique_keys=$(($(humanfriendly --parse-size="$unique_size") / (key_size + value_size)))

	"$workspace"/tests/workloads/prepare.sh "$output_dir" || return $?
	mkdir -p "$output_dir"/load
	mkdir -p "$output_dir"/warmup
	"$workspace"/tests/workloads/dbbench.sh "$db_bench_path" "$output_dir" "$num_unique_keys" "$key_size" "$value_size" \
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
	exit_code=$?
	"$workspace"/tests/helper/data-rocksdb.sh "$output_dir"
	"$workspace"/tests/helper/plot-rocksdb.sh "$output_dir"
	return $exit_code
)

load_all_run_phases() (
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
	phase_secs=$1
	shift
	phases_write_MB_s=$1
	shift
	output_dir="$workspace/data/$benchmark-key-$key_size-value-$value_size-unique-size-$unique_size-phase-secs-$phase_secs-write-MB-s-$(echo $phases_write_MB_s | tr ' ' '-')$suffix/$version"
	num_unique_keys=$(($(humanfriendly --parse-size="$unique_size") / (key_size + value_size)))

	benchmarks_json="[
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
	}"
	benchmarks_json=$(echo "$phases_write_MB_s" | tr ' ' '\n' | {
		while read write_MB_s; do
			benchmarks_json="$benchmarks_json,
	{
		\"name\": \"resetstats\"
	},
	{
		\"name\": \"$benchmark\",
		\"duration\": $phase_secs,
		\"benchmark_write_rate_limit\": $((write_MB_s * 1000000))
	},
	{
		\"name\": \"stats\"
	}"
		done
		echo "$benchmarks_json"
	})
	benchmarks_json="$benchmarks_json
]"
	echo "$benchmarks_json"

	"$workspace"/tests/workloads/prepare.sh "$output_dir" || return $?
	mkdir -p "$output_dir"/load
	"$workspace"/tests/workloads/dbbench.sh "$db_bench_path" "$output_dir" "$num_unique_keys" "$key_size" "$value_size" \
		--benchmarks_json="$benchmarks_json" \
		"$@"
	exit_code=$?
	"$workspace"/tests/helper/data-rocksdb.sh "$output_dir"
	"$workspace"/tests/helper/plot-rocksdb.sh "$output_dir"
	return $exit_code
)

meituan_writer() (
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
	output_dir=$workspace/data/$workload_name/$version

	num_unique_keys=$(($(humanfriendly --parse-size="$unique_size") / (key_size + value_size)))
	"$workspace"/tests/workloads/prepare.sh "$output_dir" || return $?
	mkdir -p "$output_dir"/load
	"$workspace"/tests/workloads/dbbench.sh "$db_bench_path" "$output_dir" "$num_unique_keys" "$key_size" "$value_size" \
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
	exit_code=$?
	"$workspace"/tests/helper/data-rocksdb.sh "$output_dir"
	"$workspace"/tests/helper/plot-rocksdb.sh "$output_dir"
	return $exit_code
)
