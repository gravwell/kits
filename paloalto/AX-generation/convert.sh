#!/bin/bash
awk -F '	' 'NR==FNR { map[$1] = $2; next }
$0 in map { $0 = map[$0] }
{ print }' map $1 \
| sed ':a;N;$!ba;s/\n/, /g'