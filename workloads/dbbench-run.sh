#!/usr/bin/env sh
if [ $# -ne 2 ]; then
	echo Usage: $0 benchmark_write_rate_limit rate_limiter_bytes_per_sec
	exit 1
fi
benchmark_write_rate_limit=$(humanfriendly --parse-size="$1")
rate_limiter_bytes_per_sec=$(humanfriendly --parse-size="$2")
workspace=$(realpath "$(dirname $0)"/../..)
output_dir="$workspace/data/rocksdb"
mkdir -p "$output_dir"

$(dirname $0)/dbbench.sh "$output_dir" \
	"--use_existing_db=true \
--benchmarks=overwrite \
--benchmark_write_rate_limit=$benchmark_write_rate_limit \
--rate_limiter_bytes_per_sec=$rate_limiter_bytes_per_sec \
--writes=10000000 \
--statistics=true \
--report_file=$output_dir/report.csv \
--report_interval_seconds=1 \
--histogram=true"
