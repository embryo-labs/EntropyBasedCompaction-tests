#!/usr/bin/env sh
if [ $# -lt 3 ]; then
	echo Usage: $0 output-dir num-unique-keys key-size args...
	exit 1
fi
. "$(dirname $0)"/common.sh
with_policy_universal $(dirname $0)/dbbench-run.sh "$@" \
	--space_amplification_percent_limit_hard=50
