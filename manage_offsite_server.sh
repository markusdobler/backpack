#!/bin/bash

set -e

HOST_LOCAL=$(hostname)
PORT_LOCAL=22
SOCKET=~/.backpack/status/backpack.${HOST_LOCAL}.uberspace.socket


function start_connection {
for i in $(seq 10)
do
    PORT_REMOTE=$((61000+RANDOM%3000))
    if ssh -M -S $SOCKET -q -o "ExitOnForwardFailure yes" -fnNT -R ${PORT_REMOTE}:localhost:${PORT_LOCAL} mado@phoenix.uberspace.de > /dev/null 2>&1
    then
        curl -s http://mado.phoenix.uberspace.de/backpack/log/port/${HOST_LOCAL}/${PORT_REMOTE}
        return
    fi
    echo "Failed on iteration $i, $PORT_REMOTE"
done
exit 1
}

function kill_connection {
    ssh -S $SOCKET -q -O exit mado@phoenix.uberspace.de 2>/dev/null
    rm -f $SOCKET
}

function restart_connection {
    kill_connection || true
    start_connection
}

case $1 in
    restart)
        restart_connection
        ;;
    ensure)
        if [ -e $SOCKET ]
        then
            DATA=$((RANDOM))
            RESPONSE=$(ssh -S $SOCKET -q mado@phoenix.uberspace.de echo $DATA)
            if [[ $? -eq 0 ]]
            then
                if  [[ "$RESPONSE" == "$DATA" ]]
                then
                    exit 0
                fi
            fi
        fi
        restart_connection
        ;;
    *)
        echo "Unknown command: '$1'."
        ;;
esac
    
