#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: $0 output-dir args...
	exit 1
fi
output_dir="$1"
shift
. $(dirname $0)/args.sh
workspace=$(realpath "$(dirname $0)"/../..)
ulimit -n 100000
# Dump core when crash
ulimit -c unlimited
export ASAN_OPTIONS="abort_on_error=1:disable_coredump=0"
cd "$output_dir"
$workspace/rocksdb/build/db_bench \
	--ttl_seconds=0 \
	--use_direct_io_for_flush_and_compaction=true \
	--use_direct_reads=true \
	--compression_type=none \
	--compression_ratio=1 \
	--bloom_bits=10 \
	--key_size=24 \
	--value_size=1000 \
	--max_background_jobs=6 \
	--block_size=16384 \
	--write_buffer_size=$memtable_size \
	--target_file_size_base=$memtable_size \
	--db="$workspace/testdb" \
	--num=100000000 \
	"$@"
