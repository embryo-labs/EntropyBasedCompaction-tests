#!/usr/bin/env sh
set -e

cd $(dirname $0)/../../rocksdb
mkdir -p build
cd build
cmake .. -DUSE_RTTI=true -DFAIL_ON_WARNINGS=OFF -DWITH_TBB=on -DCMAKE_BUILD_TYPE=None -DCMAKE_C_FLAGS="$CFLAGS -Wall -O2 -g" -DCMAKE_CXX_FLAGS="$CXXFLAGS -Wall -O2 -g" -DCMAKE_EXPORT_COMPILE_COMMANDS=1
make -j$(nproc) db_bench
cd ../..

cmake -S "SILK" -B "SILK/build" -DFAIL_ON_WARNINGS=OFF -DCMAKE_BUILD_TYPE=None -DCMAKE_C_FLAGS="$CFLAGS -Wall -O2 -g" -DCMAKE_CXX_FLAGS="$CXXFLAGS -Wall -O2 -g" -DCMAKE_EXPORT_COMPILE_COMMANDS=1
cmake --build "SILK/build" --target db_bench -j$(nproc)

cmake -S "endure" -B "endure/build" -DFAIL_ON_WARNINGS=OFF
nice cmake --build "endure/build" --target db_bench -j$(nproc)
