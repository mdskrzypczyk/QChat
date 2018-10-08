#!/usr/bin/env bash
ps aux | grep python | grep "bb84_purified" | awk {'print $2'} | xargs kill -9
python bb84_purified/aliceBB84.py &
python bb84_purified/eveBB84.py &
python bb84_purified/bobBB84.py
