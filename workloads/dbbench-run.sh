#!/usr/bin/env sh
if [ $# -lt 4 ]; then
	echo Usage: $0 output-dir command benchmark_write_rate_limit rate_limiter_bytes_per_sec args...
	exit 1
fi
output_dir=$1
shift
command=$(realpath "$1")
shift
benchmark_write_rate_limit=$(humanfriendly --parse-size="$1")
shift
rate_limiter_bytes_per_sec=$(humanfriendly --parse-size="$1")
shift
threads=16
writes=100000000
workspace=$(realpath "$(dirname $0)"/../..)
mkdir -p "$output_dir"
cd "$output_dir"
"$workspace"/tests/helper/exe-while.sh . "$command" . \
	--use_existing_db=true \
	--benchmarks=overwrite,stats \
	--soft_pending_compaction_bytes_limit=$((20 * 1000 * 1000 * 1000)) \
	--benchmark_write_rate_limit=$benchmark_write_rate_limit \
	--rate_limiter_bytes_per_sec=$rate_limiter_bytes_per_sec \
	--threads=$threads \
	--writes=$(($writes / $threads)) \
	--statistics=true \
	--report_file=report.csv \
	--report_interval_seconds=1 \
	--histogram=true \
	"$@" \
	> stdout.txt
