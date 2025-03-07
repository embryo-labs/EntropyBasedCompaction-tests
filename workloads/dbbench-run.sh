#!/usr/bin/env sh
if [ $# -ne 2 ]; then
	echo Usage: $0 benchmark_write_rate_limit rate_limiter_bytes_per_sec
	exit 1
fi
benchmark_write_rate_limit=$(humanfriendly --parse-size="$1")
rate_limiter_bytes_per_sec=$(humanfriendly --parse-size="$2")
threads=16
writes=100000000
mydir=$(realpath $(dirname $0))
workspace=$(realpath "$(dirname $0)"/../..)
output_dir="$workspace/data/rocksdb"
mkdir -p "$output_dir"
cd "$output_dir"
"$workspace"/tests/helper/exe-while.sh . sh -c "\"$mydir\"/dbbench.sh . \
	--use_existing_db=true \
	--benchmarks=overwrite,stats \
	--soft_pending_compaction_bytes_limit=$((20 * 1000 * 1000 * 1000)) \
	--benchmark_write_rate_limit=$benchmark_write_rate_limit \
	--rate_limiter_bytes_per_sec=$rate_limiter_bytes_per_sec \
	--threads=$threads \
	--writes=$(($writes / $threads)) \
	--statistics=true \
	--report_file=\"$output_dir\"/report.csv \
	--report_interval_seconds=1 \
	--histogram=true \
	> \"$output_dir\"/stdout.txt"
