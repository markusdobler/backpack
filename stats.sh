#!/bin/bash

curl --get mado.phoenix.uberspace.de/backpack/log/stats/$(hostname) \
    --data-urlencode "uptime=$(uptime -p | sed 's/^up \(\S\+\s\+[^, ]\+\),\? .*$/\1/')" \
    --data-urlencode "available=$(df /media/data/ -h --output='avail' | tail -n 1 | sed 's/ //g')" \
    --data-urlencode "segments=$(cd /media/data/borg/data/; ls $(ls | sort -n | tail -n 1) | sort -n | tail -n 1)"

    #--data-urlencode "/media/data/borg=$(du -hs /media/data/borg | sed 's/ .*//')" \
    #--data-urlencode "/media/data/borg_snapshots=$(du -hs /media/data/borg_snapshots | sed 's/ .*//')" \
