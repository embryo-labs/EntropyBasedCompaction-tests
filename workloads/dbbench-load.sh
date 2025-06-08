#!/usr/bin/env sh
if [ ! "$4" ]; then
	echo Usage: "$0" output-dir num-unique-keys key-size value-size args...
	exit 1
fi
output_dir=$1
shift
num_unique_keys=$1
shift
key_size=$1
shift
value_size=$1
shift
workspace=$(realpath "$(dirname $0)"/../..)
"$(dirname $0)"/prepare.sh "$output_dir" || return $?
"$(dirname $0)"/dbbench.sh "$output_dir" "$num_unique_keys" "$key_size" \
	--value_size="$value_size" \
	--benchmarks=filluniquerandomdeterministic,compactall,stats \
	--disable_auto_compactions=true \
	"$@" > "$output_dir"/load-stdout.txt
ret=$?
mv "$workspace"/testdb/LOG "$output_dir"/load-LOG
return $ret
