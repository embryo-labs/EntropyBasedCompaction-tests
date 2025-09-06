#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: "$0 test-dir max(MB/s) [num-readers]"
	exit 1
fi
max_MB_s=$2
if [ "$3" ]; then
	num_readers=$3
else
	num_readers=1
fi
mydir=$(realpath "$(dirname $0)")
cd "$1"
seq_read_file=test2
seq_read_size=64GiB
rand_read_file=test3
rand_read_size=64GiB
"$mydir"/../create-file.sh "$rand_read_file" "$rand_read_size"

reader_out=$(mktemp)
trap "exit 1" INT TERM
trap "pkill -P $$; rm $reader_out" EXIT

echo '['
i=0
while true; do
	echo "\
	{
		\"expected(MiB/s)\": ${i},
		\"results\": ["
	repeat=5
	while true; do
		if [ $i -gt 0 ]; then
			fio --numjobs=$num_readers --rate=$((i / num_readers))M --filename="$seq_read_file" --bs=1M --size=$seq_read_size --loops=100 --fallocate=none --ioengine=sync --direct=1 --name=test --readwrite=read --group_reporting > "$reader_out" &
			reader=$!
		else
			reader=""
		fi
		out=$(fio --rate=1M --io_size=100M --bs=16K --size=64G --filename=$rand_read_file --readwrite=randread --randrepeat=0 --ioengine=psync --direct=1 --name=test --group_reporting)
		if [ "$reader" ]; then
			kill $reader
			wait $reader
			read=$(grep "READ" $reader_out | cut -d'=' -f2 | cut -d' ' -f1)
		else
			read=0MiB/s
		fi
		echo -n "\
			{
				\"read\": \"$read\",
				\"read-latency(us)\": $(echo "$out" | grep " lat (usec): " | cut -d',' -f3 | cut -d'=' -f2)
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
	if [ $i -gt "$max_MB_s" ]; then
		echo
		break
	else
		echo ','
	fi
done
echo ']'
