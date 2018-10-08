#!/usr/bin/env bash
ps aux | grep python | grep "superdense_coding_example" | awk {'print $2'} | xargs kill -9
python qchat_example/eveTest.py &
python qchat_example/bobTest.py &
python qchat_example/aliceTest.py
