#!/usr/bin/env sh
if [ ! "$6" ]; then
	echo Usage: "$0 test-dir rand-read-numjobs rand-read-rate step(MB/s) max(MB/s) repeat"
	exit 1
fi
rand_read_numjobs=$2
rand_read_rate=$3
step_MB_s=$4
max_MB_s=$5
arg_repeat=$6
mydir=$(realpath "$(dirname $0)")
cd "$1"
seq_rw=test2
seq_rw_size=64GiB
"$mydir"/../create-file.sh "$seq_rw" "$seq_rw_size"
rand_read=test3
rand_read_size=64GiB
"$mydir"/../create-file.sh "$rand_read" "$rand_read_size"

rw_out=$(mktemp)
trap "exit 1" INT TERM
trap "pkill -P $$; rm $rw_out" EXIT

echo '['
i=0
while true; do
	echo "\
	{
		\"expected(MiB/s)\": ${i},
		\"results\": ["
	repeat=$arg_repeat
	while true; do
		if [ $i -gt 0 ]; then
			fio --rate=$((i / 2))M --filename="$seq_rw" --bs=1M --size=$seq_rw_size --readwrite=rw --loops=100 --ioengine=sync --direct=1 --name=test --group_reporting --unified_rw_reporting=mixed > "$rw_out" &
			rw=$!
		else
			rw=""
		fi
		out=$(fio --rate=$rand_read_rate --numjobs=$rand_read_numjobs --runtime=100 --bs=4K --size=$rand_read_size --filename=$rand_read --readwrite=randread --randrepeat=0 --ioengine=libaio --iodepth=32 --direct=1 --name=test --group_reporting)
		if [ "$rw" ]; then
			kill $rw
			wait $rw
			real=$(grep "MIXED" $rw_out | cut -d'=' -f2 | cut -d' ' -f1)
		else
			real=0MiB/s
		fi
		percentile() {
			echo "$out" | grep "$1" | awk -F"$1=" '{print $2}' | cut -d'[' -f2 | cut -d']' -f1
		}
		echo -n "\
			{
				\"real\": \"$real\",
				\"read-latency-avg(us)\": $(echo "$out" | grep " lat (usec): " | cut -d',' -f3 | cut -d'=' -f2),
				\"read-latency-99%(us)\": $(percentile 99.00th),
				\"read-latency-99.9%(us)\": $(percentile 99.90th),
				\"read-latency-99.99%(us)\": $(percentile 99.99th)
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
	i=$((i + step_MB_s))
	if [ $i -gt "$max_MB_s" ]; then
		echo
		break
	else
		echo ','
	fi
done
echo ']'
