#!/bin/sh

# usage ./chkver.sh <PACKAGE_VER>

CURENT_VER=`rawdata --version | sed -e 's/[^0-9]//g' | cut -b 1-8`
PACKAGE_VER=`cat $1 | sed -e 's/[^0-9]//g' | cut -b 1-8`
LOG_FP=$2

echo "Current version: $CURENT_VER" >> $LOG_FP
echo "Package version: $PACKAGE_VER" >> $LOG_FP

# if [ 10 -ge 10 ]; then echo "true"; else echo "false"; fi  # true
# if [ 10 -ge 11 ]; then echo "true"; else echo "false"; fi  # false
# if [ 10 -ge 9  ]; then echo "true"; else echo "false"; fi  # true

if [ $PACKAGE_VER -ge $CURENT_VER ]
then
   # echo "true";
   echo "chkver.sh passed!" >> $LOG_FP
   exit 0
else
   # echo "false";
   echo "chkver.sh failed!" >> $LOG_FP
   exit 127
fi


