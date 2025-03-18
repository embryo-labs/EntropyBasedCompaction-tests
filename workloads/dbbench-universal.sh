#!/usr/bin/env sh
if [ ! "$1" ]; then
	echo Usage: "$0" output-dir args...
	exit 1
fi
output_dir=$1
shift
. $(dirname $0)/args.sh
$(dirname $0)/dbbench.sh "$output_dir" \
	--compaction_style=1 \
	--num_levels=1 \
	--universal_max_size_amplification_percent=$((100 / C)) \
	--level0_file_num_compaction_trigger=$(python3 -c "import math; print(math.ceil(math.log2($s * $R)))") \
	"$@"
