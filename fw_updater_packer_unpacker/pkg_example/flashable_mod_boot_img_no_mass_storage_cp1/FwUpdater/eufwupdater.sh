#!/bin/sh

# initialization
UPDATER_BASE=$(dirname ${0})
ANIM_PID=0
EPOCH=$(date +%s)
LOG_FP=/root/updater_$EPOCH.log
echo "" > $LOG_FP

# start animation script
${UPDATER_BASE}/animation.sh $LOG_FP &
ANIM_PID=$!
sleep 2

# bypass version check
# # version check
# ${UPDATER_BASE}/chkver.sh ${UPDATER_BASE}/version $LOG_FP
# if [ "$?" -eq 0 ]
# then
#   echo "[updater.sh] version check OK" >> $LOG_FP
# else
#   echo "[updater.sh] version check NG (TBD)" >> $LOG_FP
#   # strange version Package, so we must not install this package !!
#   exit 0;
# fi
# sync

# flash customized boot img
echo "[updater.sh] writing boot.img.." >> $LOG_FP
if [ -f ${UPDATER_BASE}/boot-cp1-1.4.02.09061-mod-190411.img ] ;
then
  dd if=${UPDATER_BASE}/boot-cp1-1.4.02.09061-mod-190411.img of=/dev/mmcblk0p8 bs=4M
  sync
else
  echo "[updater.sh] desired boot.img not exit; nothing did to boot partition" >> $LOG_FP
fi

# verify the boot img success
RET=0
${UPDATER_BASE}/verify.sh ${UPDATER_BASE} $LOG_FP
if [ $? -eq 0 ]
then
  echo "[updater.sh] verify check OK" >> $LOG_FP
else
  RET=$?
  echo "[updater.sh] verify check NG, shudown, will retry upon boot up" >> $LOG_FP
fi

# # enable su in adb shell
# echo "[updater.sh] run getsu.sh" >> $LOG_FP
# ${UPDATER_BASE}/getsu.sh $LOG_FP
# if [ ! $? -eq 0 ]
# then
#   # shutdown, remove update, error occurs
#   RET=$?
# fi

sleep 2

# stop animation
if [ $ANIM_PID -ne 0 ]
then
  kill $ANIM_PID
fi

# if returned 1, will shutdown
exit $RET
