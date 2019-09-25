#!/bin/bash

# dig for the same domain multiple times in a row
# decreasing TTLs tell you which replica you hit
# time to respond tells you if that website was cached or not

filename=popular_domains.txt
starttime=$(date +%s%3N)
OLDIFS=$IFS
IFS=,
domains=()
result_file=kim_results_popular_raw.txt

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
        echo $digRes>>$result_file
    done
done