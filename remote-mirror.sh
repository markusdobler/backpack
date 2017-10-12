#!/bin/bash

set -e

HOST_REMOTE=${1:-crashpi2}
HOST_LOCAL=$(hostname)
PORT_REMOTE=$(curl -s http://mado.phoenix.uberspace.de/backpack/get/port/$HOST_REMOTE)
PORT_LOCAL=2222
SOCKET=~/.backpack/status/backpack.${HOST_LOCAL}.${HOST_REMOTE}.socket


function kill_connection {
    ssh -S $SOCKET -O exit mado@phoenix.uberspace.de 2>/dev/null
}

function start_connection {
    ssh -M -S $SOCKET -fnNT -L ${PORT_LOCAL}:localhost:${PORT_REMOTE} mado@phoenix.uberspace.de
}

# kill old session to proxy, establish new session
kill_connection || true
start_connection

# sync via proxy
rsync -a -z -e "ssh -p ${PORT_LOCAL}"  --delete --numeric-ids --delete-excluded /media/data/borg/ pi@localhost:/media/data/borg

# kill session
kill_connection
