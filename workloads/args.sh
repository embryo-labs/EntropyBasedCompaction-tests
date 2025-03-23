unique_bytes=$(humanfriendly --parse-size=10GB)

s=1
R=27
C=3

memtable_size=$(($unique_bytes / 3 / 27 / $s))
num_unique_keys=$(($unique_bytes / 1000))

leveling_num_levels=3
size=1
while [ $size -lt $R ]; do
	size=$((size * C))
	leveling_num_levels=$((leveling_num_levels + 1))
done
