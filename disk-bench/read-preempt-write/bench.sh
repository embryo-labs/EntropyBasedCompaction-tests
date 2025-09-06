#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: "$0" test-dir "max-write(MB/s)"
	exit 1
fi
test_dir=$(realpath "$1")
max_write_MB_s=$2
mydir=$(realpath "$(dirname $0)")
src_dir=$(realpath "$mydir"/../src/read-preempt-write)
cd "$src_dir"
mkdir -p build
cd build
cmake .. 1>&2
make 1>&2

cd "$test_dir"
write_file=test1
read_file=test3
"$mydir"/../create-read-file.sh "$read_file"

echo '['
i=100
while true; do
	echo "\
	{
		\"expected-write(MB/s)\": ${i},
		\"results\": ["
	repeat=5
	while true; do
		out=$("$src_dir"/build/main 100 "$write_file" ${i}e6 "$read_file" 1e6)
		echo -n "\
			{
				\"write(MB/s)\": $(echo "$out" | grep "Write" | cut -d' ' -f3),
				\"read(MB/s)\": $(echo "$out" | grep "Read" | cut -d' ' -f3),
				\"avg-read-latency(ns)\": $(echo "$out" | grep "Averate read latency" | cut -d' ' -f4)
			}"
		repeat=$(($repeat - 1))
		if [ $repeat -gt 0 ]; then
			echo ','
		else
			echo
			break
		fi
	done
	echo -n "\
		]
	}"
	i=$((i+100))
	if [ $i -gt "$max_write_MB_s" ]; then
		echo
		break
	else
		echo ','
	fi
done
echo ']'
