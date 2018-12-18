#!/bin/sh


DDAT_MOUNT_PATH=/tmp/ddat
END_USER_UPDATER_PKG=${DDAT_MOUNT_PATH}/FwUpdater.pkg




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
# End User Updater check
#########################

mount -t tmpfs tmpfs /tmp
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

