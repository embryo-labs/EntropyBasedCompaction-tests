#!/usr/bin/env sh
# RocksDB
sudo apt install -y cmake libgflags-dev libtbb-dev nlohmann-json3-dev
# tests
sudo apt install -y sysstat gawk humanfriendly

sudo apt install -y fonts-linuxlibertine
# https://stackoverflow.com/a/49884009/13688160
rm ~/.cache/matplotlib -rf
