ps aux | grep backpack-server.fcgi | grep python | sed 's/^mado\s\+\([0-9]\+\)\s.*/\1/' | xargs -n1 kill
