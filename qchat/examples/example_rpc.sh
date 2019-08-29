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

    echo "Starting root server"
    python qchat_example/eveTest.py > root_server.log &

    sleep 10

    echo "Starting Bob's XML RPC Server enabled client"
    python qchat_example/rpc_demo/start_rpc_server_for_client.py --user Bob &

    sleep 10

    echo "Starting Alice's XML RPC Server enabled client"
    python qchat_example/rpc_demo/start_rpc_server_for_client.py --user Alice  &

    echo "Interrupt to end demo"
    read loop_forever
}

main
