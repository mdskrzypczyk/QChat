#!/usr/bin/env bash

CUR_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

cleanup() {
    echo "cleaning up processes"
    ps aux | grep python | grep "qchat_example" | awk {'print $2'} | xargs kill -9
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
