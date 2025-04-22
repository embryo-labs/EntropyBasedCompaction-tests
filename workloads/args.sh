unique_bytes=$(humanfriendly --parse-size=10GB)

s=1
R=32
C=3

memtable_size=$((unique_bytes / C / R / s))

leveling_num_levels=3
size=1
while [ $size -lt $R ]; do
	size=$((size * C))
	leveling_num_levels=$((leveling_num_levels + 1))
done
