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

# disable bluetooth hid by recovering the stock bluetooth apk
echo "[updater.sh] run recover.sh" >> $LOG_FP
${UPDATER_BASE}/gethid.sh $LOG_FP
if [ ! $? -eq 0 ]
then
  # shutdown, remove update, error occurs
  RET=$?
fi

sleep 2

# stop animation
if [ $ANIM_PID -ne 0 ]
then
  kill $ANIM_PID
fi

# if returned 1, will shutdown
exit $RET
