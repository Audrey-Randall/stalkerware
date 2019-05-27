#!/bin/bash

#if [ $# -eq 0 ]
#then
#	echo "What domain?"
#	exit 1
#fi

INPUT=alexa_500.csv
OLDIFS=$IFS
IFS=,
domains=()
retries=1
attempt=0

[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
while read idx domain
do
	#echo "Domain : $domain"
	domains=("${domains[@]}" "$domain")
done < $INPUT
IFS=$OLDIFS

for d in ${domains[@]}; do
	while [ $attempt -lt $retries ];
	do 
	#	echo "$d"
		dig @8.8.8.8 "www.$d" +norecurse
		#sleep 1
		attempt=$((attempt+1))
	done
	attempt=0
done
