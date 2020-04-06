#!/bin/sh

# initialization
UPDATER_BASE=$(dirname ${0})
ANIM_PID=0
EPOCH=$(date +%s)
LOG_FP=/root/updater_bootimg_$EPOCH.log
echo "" > $LOG_FP

# start animation script
${UPDATER_BASE}/animation.sh $LOG_FP &
ANIM_PID=$!
sleep 2

# flash customized boot img
echo "[updater.sh] writing boot.img.." >> $LOG_FP
if [ -f ${UPDATER_BASE}/boot-1.6.50.14130-mod-200405-233932.img ] ;
then
  dd if=${UPDATER_BASE}/boot-1.6.50.14130-mod-200405-233932.img of=/dev/mmcblk0p8 bs=4M
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

sleep 2

# stop animation
if [ $ANIM_PID -ne 0 ]
then
  kill $ANIM_PID
fi

# if returned 1, will shutdown
exit $RET
