unique_bytes=$(humanfriendly --parse-size=10GB)

s=1
R=256
C=3

memtable_size=$((unique_bytes / C / R / s))

with_policy_leveling() {
	"$@" \
		--level_compaction_dynamic_level_bytes=true \
		--level0_file_num_compaction_trigger=$s \
		--max_bytes_for_level_multiplier=$C
}
with_policy_universal() {
	"$@" \
		--compaction_style=1 \
		--num_levels=1 \
		--universal_max_size_amplification_percent=$((100 / C)) \
		--level0_file_num_compaction_trigger=$(python3 -c "import math; print(math.ceil(math.log2($s * $R)))")
}
