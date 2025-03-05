#!/usr/bin/env sh

work() {
	cd ../../../testdb/
	echo Timestamp\(ns\) size
	while true; do
		echo -n "$(date +%s%N) "
		du -sb . | awk '{print $1}' | xargs echo
		sleep 1
	done
}
if [ $1 ]; then
	work > $1/du.sh.txt
else
	work
fi
