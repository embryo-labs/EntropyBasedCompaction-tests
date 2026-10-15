#!/usr/bin/env sh
cd ../..
mkdir -p testdb
mkdir -p data
git clone https://github.com/embryo-labs/EntropyBasedCompaction.git rocksdb
git clone https://github.com/embryo-labs/EntropyBasedCompaction-baseline-Endure.git endure
git clone https://github.com/embryo-labs/EntropyBasedCompaction-baseline-SILK.git SILK
