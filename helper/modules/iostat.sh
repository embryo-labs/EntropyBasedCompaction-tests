process() {
	# mawk does not respect fflush(stdout)
	# Use sh -c to ensure that "date" is executed for every line
	gawk "
		{
			if (\"$1\" == \$1) {
					print \$2,\$3,\$8,\$9,\$23
					fflush(stdout)
			}
		}
	" | xargs -I {} sh -c 'echo $(date +%s%N) {}'
}

