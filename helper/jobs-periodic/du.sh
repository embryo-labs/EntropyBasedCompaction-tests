#!/usr/bin/env sh

work() {
	cd ../../../
	echo Timestamp\(ns\) size
	while true; do
		if out=$(du -sb testdb 2> /dev/null); then
			echo -n "$(date +%s%N) "
			echo "$out" | awk '{print $1}' | xargs echo
		fi
		sleep 1
	done
}
if [ $1 ]; then
	work > $1/du.sh.txt
else
	work
fi
