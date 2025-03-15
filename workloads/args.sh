s=5
R=27
C=3
memtable_size=$(($(humanfriendly --parse-size=100GB) / 3 / 27 / $s))

leveling_num_levels=3
size=1
while [ $size -lt $R ]; do
	size=$((size * C))
	leveling_num_levels=$((leveling_num_levels + 1))
done
