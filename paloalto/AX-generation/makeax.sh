#!/bin/bash
rm palo.ax
for i in *.txt
do
	# generate the CSV "params"
	NAME=`basename -s .txt $i`
	# now build the AX TOML file
	echo '[[extraction]]' >> palo.ax
	echo name = \"Palo Alto $NAME\" >> palo.ax
	echo tag = \"pan_$NAME\" >> palo.ax
	echo desc = \"Palo Alto $NAME log format\" >> palo.ax
	echo module = \"csv\" >> palo.ax
	echo params = \"`./convert.sh $i`\" >> palo.ax
	echo >> palo.ax
done
cat palo.ax
