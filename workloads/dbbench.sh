#!/usr/bin/env bash
if [ ! "$5" ]; then
	echo Usage: $0 db_bench_path output-dir num-unique-keys key-size value-size args...
	exit 1
fi
db_bench_path=$1
shift
output_dir=$(realpath "$1")
shift
num_unique_keys=$1
shift
key_size=$1
shift
value_size=$1
shift
workspace=$(realpath "$(dirname $0)"/../..)
echo Output dir: "$output_dir"

ulimit -n 524288
# Dump core when crash
ulimit -c unlimited
export ASAN_OPTIONS="abort_on_error=1:disable_coredump=0"
cd "$output_dir"
"$workspace"/tests/helper/exe-while . $db_bench_path \
	--ttl_seconds=0 \
	--use_direct_io_for_flush_and_compaction=true \
	--use_direct_reads=true \
	--compression_type=none \
	--compression_ratio=1 \
	--bloom_bits=10 \
	--key_size="$key_size" \
	--block_size=4096 \
	--value_size="$value_size" \
	--enable_pipelined_write=false \
	--unordered_write=true \
	--auto_readahead_size=true \
	--db="$workspace/testdb" \
	--num=$num_unique_keys \
	--level0_slowdown_writes_trigger=100000 \
	--level0_stop_writes_trigger=100000 \
	--soft_pending_compaction_bytes_limit=1000000000000000 \
	--hard_pending_compaction_bytes_limit=1000000000000000 \
	--ops_between_duration_checks=1 \
	--statistics=true \
	--report_file=report.csv \
	--report_interval_seconds=1 \
	--histogram=true \
	"$@" \
	> stdout.txt
exit_code=$?
if [ "$exit_code" -ne 0 ]; then
	echo "exe-while failed with exit code $exit_code" >&2
	echo $exit_code > "$output_dir"/exe-while-exit-code
	exit "$exit_code"
fi
if [ "$with_perf" ] && [ "$with_perf" -gt 0 ]; then
	perf script -i perf.data -f | inferno-collapse-perf | $FlameGraphPath/flamegraph.pl > perf.svg
fi
if [ "$with_offcputime" ] && [ "$with_offcputime" -gt 0 ]; then
	$FlameGraphPath/flamegraph.pl --color=io --title="Off-CPU Time Flame Graph" --countname=us < offcputime.stacks > offcputime.svg
fi
