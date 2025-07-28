#!/usr/bin/env bash
if [ ! "$3" ]; then
	echo Usage: $0 output-dir num-unique-keys key-size args...
	exit 1
fi
output_dir=$(realpath "$1")
shift
num_unique_keys=$1
shift
key_size=$1
shift
workspace=$(realpath "$(dirname $0)"/../..)

ulimit -n 100000
# Dump core when crash
ulimit -c unlimited
export ASAN_OPTIONS="abort_on_error=1:disable_coredump=0"
cd "$output_dir"
command=("$workspace"/tests/helper/exe-while.sh .)
if [ "$with_perf" ] && [ "$with_perf" -gt 0 ]; then
	command+=(perf record --call-graph=fp -o "$output_dir"/perf.data)
fi
"${command[@]}" "$workspace"/rocksdb/build/db_bench \
	--ttl_seconds=0 \
	--use_direct_io_for_flush_and_compaction=true \
	--use_direct_reads=true \
	--compression_type=none \
	--compression_ratio=1 \
	--bloom_bits=10 \
	--key_size="$key_size" \
	--max_background_jobs=6 \
	--block_size=4096 \
	--enable_pipelined_write=false \
	--unordered_write=true \
	--db="$workspace/testdb" \
	--num=$num_unique_keys \
	--level0_slowdown_writes_trigger=100000 \
	--level0_stop_writes_trigger=100000 \
	--statistics=true \
	--report_file=report.csv \
	--report_interval_seconds=1 \
	--histogram=true \
	"$@" \
	> stdout.txt
if [ "$with_perf" ] && [ "$with_perf" -gt 0 ]; then
	perf script -i perf.data -f | inferno-collapse-perf > perf.folded
fi
