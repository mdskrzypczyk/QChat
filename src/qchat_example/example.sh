#!/usr/bin/env bash

CUR_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

cleanup() {
    PIDS=$(ps aux | grep python | grep "qchat_example" | awk {'print $2'} | tr '\n' ' ')
    if test PIDS != ""
    then
        echo "Cleaning up processes $PIDS"
        kill -9 $PIDS
    fi
}

main () {
    trap cleanup EXIT

    cleanup

    pushd "$(realpath ${CUR_DIR}/../)"

    python qchat_example/eveTest.py &
    python qchat_example/bobTest.py &
    python qchat_example/aliceTest.py
}

main
