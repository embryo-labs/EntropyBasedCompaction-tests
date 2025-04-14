#!/usr/bin/env sh
if [ ! "$3" ]; then
	echo Usage: $0 output-dir num-unique-keys key-size args...
	exit 1
fi
output_dir=$1
shift
num_unique_keys=$1
shift
key_size=$1
shift
. $(dirname $0)/args.sh
workspace=$(realpath "$(dirname $0)"/../..)

if [ "$s" -gt 1 ]; then
	main_level_size_threshold=$((memtable_size + memtable_size / 10))
else
	main_level_size_threshold=0
fi

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
	--key_size="$key_size" \
	--max_background_jobs=6 \
	--block_size=16384 \
	--write_buffer_size=$memtable_size \
	--target_file_size_base=$memtable_size \
	--db="$workspace/testdb" \
	--num=$num_unique_keys \
	--main_level_size_threshold="$main_level_size_threshold" \
	"$@"
