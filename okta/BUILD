#!/bin/bash
#
#
#
# To build the kit you will need the Gravwell kitctl command
# If you have a functioning Go build environment execute the following command:
#	go install github.com/gravwell/gravwell/v3/kitctl
#
#
# Then "pack" the kit into a kit file by executing the "pack" kitctl command
#
#
# You can also just execute this file using bash
#
#
OUT = okta.kit

cmd=$(which kitctl)
if [ "$?" != "0" ]; then
	echo "Missing the kitctl command"
	exit -1
fi


set -e
$cmd pack $OUT