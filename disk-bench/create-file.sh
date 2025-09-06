#!/usr/bin/env sh
if [ ! "$2" ]; then
	echo Usage: "$0" file size
	exit 1
fi
file=$1
size=$(humanfriendly --parse-size="$2")

if [ ! -f "$file" ] || [ $(wc -c < "$file") -lt "$size" ]; then
	fio --bs=1M --size=$size --filename=$file --fallocate=none --ioengine=sync --direct=1 --name=test --readwrite=write --group_reporting 1>&2
fi
