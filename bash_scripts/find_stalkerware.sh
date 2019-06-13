#!/bin/bash

# dig for the same domain multiple times in a row
# decreasing TTLs tell you which replica you hit
# time to respond tells you if that website was cached or not

filename=stalkerware_domains.txt
starttime=$(date +%s%3N)
OLDIFS=$IFS
IFS=,
domains=()

[ ! -f $filename ] && { echo "$filename file not found"; exit 99; }
while read domain
do
        # echo "Domain: $domain"
        domains=("${domains[@]}" "$domain")
done < $filename
IFS=$OLDIFS

while true; do
	for d in ${domains[@]}; do
		digRes=`dig @8.8.8.8 $d +norecurse`
		servfail=`echo $digRes | grep -o "SERVFAIL"`
		skip=$?
		if [ "$skip" -eq "0" ]
		then
			echo "Servfail"
			sleep 1.0
			continue
		fi
		ms=`echo $digRes | grep -o "Query time: .* msec" | grep -o "[0-9]*"`
		ttl=`echo $digRes | grep -o "ANSWER SECTION:\s\S*\s[0-9]*\sIN\sA" | grep -o "\s[0-9]*\s"`
		timeElapsed=$(($(date +%s%3N)-starttime))
		echo "Domain: " $d " TTL:" $ttl 
		sleep 1.0
	done
done

