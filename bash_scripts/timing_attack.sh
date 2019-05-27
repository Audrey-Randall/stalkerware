#!/bin/bash

# dig for the same domain multiple times in a row
# decreasing TTLs tell you which replica you hit
# time to respond tells you if that website was cached or not

echo response_time, ttl > timing_attack.csv
while true
do
	digRes=`dig @8.8.8.8 facebook.com`
	ms=`echo $digRes | grep -o "Query time: .* msec" | grep -o "[0-9]*"`
	ttl=`echo $digRes | grep -o "ANSWER SECTION:\sfacebook\.com\.\s[0-9]*\sIN\sA" | grep -o "[0-9]*"`
	echo $ms, $ttl >> timing_attack.csv
	sleep 1
done

