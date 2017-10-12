#!/bin/bash

set -e

COUNTER_FILE=~/.backpack/status/rsnapshot.counter
COUNTER=$(cat "$COUNTER_FILE" 2>/dev/null || echo "1")
echo $(($COUNTER+1)) > $COUNTER_FILE

rsnapshot -v -c ~/.backpack/conf/rsnapshot.conf sync

# perform rotation on level #L every pow(4, #L) iterations
for level in $(seq 9 -1 0)
do
    if [[ $(( $COUNTER % (4**$level) )) == 0 ]]
    then
        echo "counter ${COUNTER}, level $level"
        rsnapshot -v -c ~/.backpack/conf/rsnapshot.conf level${level}
    fi
done

