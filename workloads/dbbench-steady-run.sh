#!/usr/bin/env sh
if [ $# -lt 3 ]; then
	echo Usage: $0 output-dir benchmark_write_rate_limit rate_limiter_bytes_per_sec args...
	exit 1
fi
output_dir=$1
shift
benchmark_write_rate_limit=$(humanfriendly --parse-size="$1")
shift
rate_limiter_bytes_per_sec=$(humanfriendly --parse-size="$1")
shift
. $(dirname $0)/args.sh
k=$(echo "1 / ($rate_limiter_bytes_per_sec / $benchmark_write_rate_limit - 2)" | bc -l)
policy_file=$(mktemp)
trap "exit 1" INT TERM
trap "rm $policy_file" EXIT
$(dirname $0)/../helper/solver.py -s=$s -k=$k -R=$R -C=$C --export-policy="$policy_file"
a=$(jq -r ".a" < "$policy_file")
cp "$policy_file" /tmp/policy-file
echo ./solver.py -s=$s -k=$k -R=$R -C=$C --print-path > /tmp/solve.sh
$(dirname $0)/../helper/solver.py -s=$s -k=$k -R=$R -C=$C --print-path > /tmp/policy-path
$(dirname $0)/dbbench-run.sh "$output_dir" "$(dirname $0)"/dbbench.sh "$benchmark_write_rate_limit" \
	--rate_limiter_bytes_per_sec="$rate_limiter_bytes_per_sec" \
	--compaction_style=3 \
	--compaction_policy="steady" \
	--steady_policy_file="$policy_file" \
	--num_levels=3 \
	--level0_slowdown_writes_trigger="$a" \
	"$@"
