#!/usr/bin/env sh
if [ $# -lt 4 ]; then
	echo Usage: $0 output-dir command num-unique-keys key-size args...
	exit 1
fi
output_dir=$1
shift
command=$(realpath "$1")
shift
num_unique_keys=$1
shift
key_size=$1
shift
. $(dirname $0)/args.sh
workspace=$(realpath "$(dirname $0)"/../..)
mkdir -p "$output_dir"
cd "$output_dir"
"$workspace"/tests/helper/exe-while.sh . "$command" . "$num_unique_keys" "$key_size" \
	--use_existing_db=true \
	--soft_pending_compaction_bytes_limit=$(( \
		unique_bytes / (C * R) * ( \
			2 + (leveling_num_levels - 2) * (C + 1) \
		) * 3/2 \
	)) \
	--writes=$num_unique_keys \
	--finish_after_writes=1 \
	--statistics=true \
	--report_file=report.csv \
	--report_interval_seconds=1 \
	--histogram=true \
	"$@" \
	> stdout.txt
