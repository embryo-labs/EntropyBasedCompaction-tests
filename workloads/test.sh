#!/usr/bin/env sh
workspace=$(realpath "$(dirname $0)"/../..)
. $(dirname $0)/common.sh
nice $(dirname $0)/../helper/build.sh

compaction_MB_s=200
read_workload() {
	with_nexts 48 with_meituan_ratio with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB no_stall "$@"
}

key_size=16
value_size=603
unique_size=10GB
warmup_secs=1200
run_secs=1200
for write_MB_s in 10 30 50; do
	read_workload with_write_MB_s $write_MB_s with_policy_rocksdb_tuned load_all_warmup_run rocksdb-tuned readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_policy_universal_hard_trigger load_all_warmup_run universal-hard-trigger readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs

	for ratio in 2 4 8; do
		read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_tiering $ratio load_all_warmup_run tiering$ratio readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	done

	# Soft-preemption
	read_workload with_write_MB_s $write_MB_s with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs

	# Only-by-entropy
	read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_entropy_based preempt_only_by_entropy 0 load_all_warmup_run preempt_only_by_entropy-be-0 readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs

	# Only-by-num
	read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_entropy_based preempt_only_by_num load_all_warmup_run preempt_only_by_num readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs

	# No-exclude-small
	read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_entropy_based no_exclude_small load_all_warmup_run no_exclude_small readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done

for write_MB_s in 10 20 30 40 50 60; do
	read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done

for write_MB_s in 10 20 30 40 50 60; do
	read_workload with_write_MB_s $write_MB_s autotune_entropy_threshold with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 0 1 2 3 4 5 6; do
	read_workload with_write_MB_s 10 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 0 0.5 0.9 1 2 3 4 5 6; do
	read_workload with_write_MB_s 20 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 0 1 1.5 1.6 2 2.5 3 4 5 6; do
	read_workload with_write_MB_s 3 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 0 1 1.5 2 2.3 2.5 2.8 3 3.5 4 5 6; do
	read_workload with_write_MB_s 40 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 2.5 3 3.1 3.2 3.5 4 5 6; do
	read_workload with_write_MB_s 50 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
for t_e in 3.7 3.8 3.9 4 4.5 5 5.5 6; do
	read_workload with_write_MB_s 60 with_entropy_threshold $t_e with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done

for t_e in 0 0.5 1 2 3; do
	for write_MB_s in 10 20 30 40 50 60; do
		read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_entropy_threshold $t_e with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	done
done

for k_n in 1.1 1.4 2 4 8 16 32 64; do
	for write_MB_s in 10 50; do
		read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_k_n $k_n with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	done
done

for io_sa in 10 30 50 70 90; do
	for write_MB_s in 30 50; do
		read_workload with_write_MB_s $write_MB_s with_io_sa_limit_MB_s $io_sa with_max_running_background_jobs 1 with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	done
done

write_MB_s=50
for zipfian_theta in 0.5 0.8 0.9 0.99; do
	read_workload with_write_MB_s $write_MB_s with_write_zipfian_theta $zipfian_theta autotune_entropy_threshold with_policy_entropy_based no_preemption_conditions load_all_warmup_run no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_write_zipfian_theta $zipfian_theta with_max_running_background_jobs 1 with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done

for write_MB_s in 10 30; do
	value_size_KB=16
	read_workload with_write_MB_s $write_MB_s with_policy_rocksdb_tuned load_all_warmup_run rocksdb-tuned readwhilewriting $key_size $((value_size_KB * 1000)) $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_tiering 4 load_all_warmup_run tiering4 readwhilewriting $key_size $((value_size_KB * 1000)) $unique_size $warmup_secs $run_secs
	for value_size_KB in 1 2 4 8 16; do
		read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $((value_size_KB * 1000)) $unique_size $warmup_secs $run_secs
	done
done

phase_secs=3600
phases_write_MB_s="10 30 50 30 10"
read_workload autotune_entropy_threshold with_policy_entropy_based no_preemption_conditions load_all_run_phases no_preemption_conditions readwhilewriting $key_size $value_size $unique_size $phase_secs "$phases_write_MB_s"
read_workload with_max_running_background_jobs 1 with_entropy_threshold 0 with_policy_entropy_based load_all_run_phases entropy-based readwhilewriting $key_size $value_size $unique_size $phase_secs "$phases_write_MB_s"

unique_size=10GB
period_secs=$((3600 * 3))
num_shards=5
for type in peak normal; do
	read_workload with_policy_rocksdb_tuned meituan_writer rocksdb-tuned $type $period_secs $num_shards $unique_size
	read_workload with_policy_universal_hard_trigger meituan_writer universal-hard-trigger $type $period_secs $num_shards $unique_size

	for ratio in 2 4 8; do
		read_workload with_max_running_background_jobs 1 with_policy_tiering $ratio meituan_writer tiering$ratio $type $period_secs $num_shards $unique_size
	done
	read_workload with_max_running_background_jobs 1 with_policy_lazy_leveling 2 3 meituan_writer lazy-leveling-2-3 $type $period_secs $num_shards $unique_size
	read_workload with_max_running_background_jobs 1 with_policy_bush meituan_writer bush $type $period_secs $num_shards $unique_size
	read_workload with_max_running_background_jobs 1 with_policy_vertiorizon 5 4 meituan_writer vertiorizon-5-4 $type $period_secs $num_shards $unique_size

	read_workload with_max_running_background_jobs 1 with_policy_entropy_based meituan_writer entropy-based $type $period_secs $num_shards $unique_size
done

# 64MiB memtable
read_workload() {
	with_nexts 48 with_meituan_ratio with_compaction_limit_MB_s $compaction_MB_s no_stall "$@"
}
unique_size=100GB
warmup_secs=$((3 * 3600))
run_secs=$((3 * 3600))
for write_MB_s in 10 30; do
	read_workload with_write_MB_s $write_MB_s with_policy_rocksdb_tuned load_all_warmup_run rocksdb-tuned readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_tiering 4 load_all_warmup_run tiering4 readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	read_workload with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done

delete_heavy() {
	# One put before one delete
	suffix="-delete-heavy$suffix" with_nexts 48 with_meituan_ratio with_compaction_limit_MB_s $compaction_MB_s with_memtable_size 8MiB no_stall "$@" \
		--expand_range_tombstones=true \
		--writes_per_range_tombstone=1 \
		--range_tombstone_width=1
}
unique_size=10GB
warmup_secs=1200
run_secs=1200
for write_MB_s in 10 30; do
	delete_heavy with_write_MB_s $write_MB_s with_policy_rocksdb_tuned load_all_warmup_run rocksdb-tuned readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	delete_heavy with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_tiering 4 load_all_warmup_run tiering4 readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
	delete_heavy with_write_MB_s $write_MB_s with_max_running_background_jobs 1 with_policy_entropy_based load_all_warmup_run entropy-based readwhilewriting $key_size $value_size $unique_size $warmup_secs $run_secs
done
