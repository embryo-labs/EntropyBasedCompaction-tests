#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: $0 output-dir args...
	exit 1
fi
output_dir="$1"
shift
memtable_size=$(humanfriendly --parse-size=200MB)
s=4
T=5
workspace=$(realpath "$(dirname $0)"/../..)
ulimit -n 100000
# Dump core when crash
ulimit -c unlimited
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
	--level0_file_num_compaction_trigger=$s \
	--max_bytes_for_level_base=$(($memtable_size * $s)) \
	--max_bytes_for_level_multiplier=$T \
	--num_levels=5 \
	--db="$workspace/testdb" \
	--num=100000000 \
	"$@"
