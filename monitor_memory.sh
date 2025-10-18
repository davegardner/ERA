#!/bin/bash
while true; do
    echo "$(date '+%H:%M:%S') - Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}') - Processes: $(ps aux | grep python | grep -v grep | wc -l)"
    sleep 5
done
