#!/bin/bash

# dig for the same domain multiple times in a row
# decreasing TTLs tell you which replica you hit
# time to respond tells you if that website was cached or not

filename=timing_attack_rate_limited.csv
echo response_time, ttl, time_elapsed > $filename
starttime=$(date +%s%3N)
while true
do
	digRes=`dig @8.8.8.8 facebook.com`
	ms=`echo $digRes | grep -o "Query time: .* msec" | grep -o "[0-9]*"`
	ttl=`echo $digRes | grep -o "ANSWER SECTION:\sfacebook\.com\.\s[0-9]*\sIN\sA" | grep -o "[0-9]*"`
	timeElapsed=$(($(date +%s%3N)-starttime))
	echo $ms, $ttl, $timeElapsed >> $filename
	sleep 0.1
done

