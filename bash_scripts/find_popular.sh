#!/bin/bash

# dig for the same domain multiple times in a row
# decreasing TTLs tell you which replica you hit
# time to respond tells you if that website was cached or not

filename=popular_domains.txt
starttime=$(date +%s%3N)
OLDIFS=$IFS
IFS=,
domains=()
result_file=kim_results_popular.txt

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
			# echo "Servfail"
			sleep 1.0
			continue
		fi
		ms=`echo $digRes | grep -o "Query time: .* msec" | grep -o "[0-9]*"`
		cname=`echo $digRes | grep -o "CNAME"`
		cname=$?
		if [ "$cname" -eq "1" ]
		then
			# This is an A record
			ttl=`echo $digRes | grep -o "ANSWER SECTION:\s\S*\s[0-9]*\sIN\sA" | grep -o "\s[0-9]*\s"`
			echo "A,"$d","$ttl","`date +%s`>>$result_file
		else
			# This is a CNAME record. Record both the CNAME TTL and the A record TTL.
			cname_ttl=`echo $digRes | grep -o "ANSWER SECTION:\s\S*\s[0-9]*\sIN\sCNAME" | grep -o "\s[0-9]*\s"`	
			ttl=`echo $digRes | grep -o "CNAME\s*\S*\s\S*\s[0-9]*\sIN\sA" | grep -o "\s[0-9]*\s"`
			a_record=`echo $digRes | grep -o "CNAME\s*\S*\s" | grep  -o "\s\S*"`
			echo "CNAME,"$d","$cname_ttl","`date +%s`>>$result_file
			echo "A,"$a_record","$ttl","`date +%s`>>$result_file
		fi
		# timeElapsed=$(($(date +%s%3N)-starttime))
		sleep 1.0
	done
done

