#!/usr/bin/env sh
if [ ! "$3" ]; then
	echo Usage: "$0 test-dir step(MB/s) max(MB/s)"
	exit 1
fi
step_MB_s=$2
max_MB_s=$3
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
	repeat=5
	while true; do
		if [ $i -gt 0 ]; then
			fio --rate=$((i / 2))M --filename="$seq_rw" --bs=1M --size=$seq_rw_size --readwrite=rw --loops=100 --ioengine=sync --direct=1 --name=test --group_reporting --unified_rw_reporting=mixed > "$rw_out" &
			rw=$!
		else
			rw=""
		fi
		out=$(fio --numjobs=32 --runtime=100 --bs=4K --size=$rand_read_size --filename=$rand_read --readwrite=randread --randrepeat=0 --ioengine=psync --direct=1 --name=test --group_reporting)
		if [ "$rw" ]; then
			kill $rw
			wait $rw
			real=$(grep "MIXED" $rw_out | cut -d'=' -f2 | cut -d' ' -f1)
		else
			real=0MiB/s
		fi
		echo -n "\
			{
				\"compaction\": \"$real\",
				\"rand-read\": $(echo "$out" | grep "READ" | cut -d'=' -f2 | cut -d' ' -f1)
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
