#!/usr/bin/env sh
if [ $# -lt 1 -o $# -gt 2 ]; then
	echo Usage: $0 output-dir \[args\]
	exit 1
fi
memtable_size=$(humanfriendly --parse-size=80MB)
workspace=$(realpath "$(dirname $0)"/..)
ulimit -n 100000
# Dump core when crash
ulimit -c unlimited
cd "$1"
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
	--threads=16 \
	--write_buffer_size=$memtable_size \
	--target_file_size_base=$memtable_size \
	--level0_file_num_compaction_trigger=10 \
	--max_bytes_for_level_base=$(($memtable_size * 10)) \
	--max_bytes_for_level_multiplier=5 \
	--num_levels=4 \
	--db="$workspace/testdb" \
	--num=100000000 \
	$2
