#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: "$0 test-dir max-write(MB/s) [num-writers]"
	exit 1
fi
max_write_MB_s=$2
if [ "$3" ]; then
	num_writers=$3
else
	num_writers=1
fi
mydir=$(realpath "$(dirname $0)")
cd "$1"
write_dir=write-dir
rand_read_file=test3
rand_read_size=64GiB
"$mydir"/../create-file.sh "$rand_read_file" "$rand_read_size"

writer_out=$(mktemp)
trap "exit 1" INT TERM
trap "pkill -P $$; rm $writer_out; rm -rf $write_dir" EXIT

echo '['
#i=0
i=100
while true; do
	echo "\
	{
		\"expected-write(MiB/s)\": ${i},
		\"results\": ["
	repeat=5
	while true; do
		rm -rf "$write_dir"
		mkdir -p "$write_dir"
		if [ $i -gt 0 ]; then
			fio --numjobs=$num_writers --rate=$((i / num_writers))M --directory="$write_dir" --bs=1M --size=1T --fallocate=none --ioengine=sync --direct=1 --name=test --readwrite=write --group_reporting > "$writer_out" &
			writer=$!
		else
			writer=""
		fi
		out=$(fio --rate=1M --io_size=100M --bs=16K --size=64G --filename=$rand_read_file --readwrite=randread --randrepeat=0 --ioengine=psync --direct=1 --name=test --group_reporting)
		if [ "$writer" ]; then
			kill $writer
			wait $writer
			write=$(grep "WRITE" $writer_out | cut -d'=' -f2 | cut -d' ' -f1)
		else
			write=0MiB/s
		fi
		echo -n "\
			{
				\"write\": \"$write\",
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
	if [ $i -gt "$max_write_MB_s" ]; then
		echo
		break
	else
		echo ','
	fi
done
echo ']'
