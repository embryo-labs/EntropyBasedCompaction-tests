unique_bytes=$(humanfriendly --parse-size=10GB)

s=1
R=32
C=3

memtable_size=$((unique_bytes / C / R / s))
