#!/bin/sh


DDAT_MOUNT_PATH=/tmp/ddat
END_USER_UPDATER_PKG=${DDAT_MOUNT_PATH}/FwUpdater.pkg
HOME_DETECTION_TMPF=/tmp/homeKeyDeect.log



# $1 : reboot=1, shutdown 0
local_reboot()
{
  umount $DDAT_MOUNT_PATH
  sync
  sync
  mount -o remount,ro /
  if [ $1 -eq 1 ]
  then
    /sbin/reboot
  else
    /sbin/poweroff
  fi

  while [ 1 ]
  do
   sleep 3
  done
}


#########################
# mount tmp file system
#########################
mount -t tmpfs tmpfs /tmp

#########################
# Home Button check
#########################

# animation hint
epd_fb_test gray DU PART 0 && \
epd_fb_test gray GC16 PART 10 0 50 50 150 50 && \
sleep 1 && \
epd_fb_test gray GC16 PART 10 0 50 150 150 50 && \
sleep 1 && \
epd_fb_test gray GC16 PART 10 0 50 250 150 50 && \
sleep 1 &

# keyscan check
busybox script -c "timeout -t 3 keyscan" -f -q ${HOME_DETECTION_TMPF}
grep -Fq "HOME" ${HOME_DETECTION_TMPF}
if [ $? -eq 0 ]
then
  rm ${HOME_DETECTION_TMPF}
  epd_fb_test gray GC16 PART 10 0 50 50 150 250
  initctl start diag
  exit 0
else
  rm ${HOME_DETECTION_TMPF}
fi

#########################
# End User Updater check
#########################

mkdir ${DDAT_MOUNT_PATH}
mount /dev/mmcblk0p16 ${DDAT_MOUNT_PATH}
if [ -f ${END_USER_UPDATER_PKG} ]
then
  rawdata --get_dump=sig_key > /tmp/sig.key
  rawdata --get_dump=dec_key > /tmp/dec.key
  start_eufwupdater.sh ${END_USER_UPDATER_PKG} /tmp /tmp/sig.key /tmp/dec.key
  ret=$?
  if [ $ret -eq 0 ]
  then
    # remove pkg, change normal boot and reboot
    change_boot_mode.sh normal
    rm -rf ${END_USER_UPDATER_PKG}
    local_reboot 1
  # elif [ $ret -eq 1 ]
  # then
  #   # remain pkg, keep boot mode and shutdown
  #   local_reboot 0
  else
    # remove pkg, change normal boot and shutdown
    change_boot_mode.sh normal
    rm -rf ${END_USER_UPDATER_PKG}
    local_reboot 0
  fi
fi

umount ${DDAT_MOUNT_PATH}

#########################
# Diag check
#########################

initctl start diag
exit 0

