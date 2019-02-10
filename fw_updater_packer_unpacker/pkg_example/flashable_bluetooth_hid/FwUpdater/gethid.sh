#!/bin/sh

# initialization
UPDATER_BASE=$(dirname ${0})
TAG="[gethid.sh]"
LOG_FP=$1

BLU_APK=${UPDATER_BASE}/bluetooth/Bluetooth.apk
BLUE_ODEX=${UPDATER_BASE}/bluetooth/Bluetooth.odex

SYSTMP=${UPDATER_BASE}/systmp
SYSBLUAPP=${SYSTMP}/app/Bluetooth
BLK09="/dev/mmcblk0p9"

# funcs
log_print() {
  echo $TAG $1 >> $LOG_FP
}

cp_perm() {
  log_print "copy from $4 to $5 w. perm $1.$2 $3"
  rm -f $5
  if [ -f "$4" ]; then
    cat $4 > $5
    set_perm $1 $2 $3 $5
  fi
}

set_perm() {
  log_print "set perm $1.$2 $3 for $4"
  chown $1.$2 $4
  chown $1:$2 $4
  chmod $3 $4
}

# check file existence
if ! [ -f $BLU_APK -a -f $BLUE_ODEX ]
then
  log_print "missing necessary files.."
  exit 2
fi

# mount system
mkdir -p $SYSTMP >> $LOG_FP 2>&1
mount $BLK09 $SYSTMP >> $LOG_FP 2>&1

if [ ! $? -eq 0 ]
then
  log_print "failed to mount system partition"
  umount $SYSTMP >> $LOG_FP 2>&1
  exit 2
fi
log_print "system partition mounted"

if [ ! -f "${SYSBLUAPP}/Bluetooth.apk_bak" ]
then
  log_print "backing up stock bluetooth files"
  mv ${SYSBLUAPP}/Bluetooth.apk ${SYSBLUAPP}/Bluetooth.apk_bak
  mv ${SYSBLUAPP}/arm/Bluetooth.odex ${SYSBLUAPP}/arm/Bluetooth.odex_bak
else
  log_print "stock bluetooth files already exist.."
  rm -f ${SYSBLUAPP}/Bluetooth.apk
  rm -f ${SYSBLUAPP}/arm/Bluetooth.odex
fi

log_print "copying new bluetooth files.."
cp_perm 0 0 0644 ${BLU_APK} ${SYSBLUAPP}/Bluetooth.apk
cp_perm 0 0 0644 ${BLUE_ODEX} ${SYSBLUAPP}/arm/Bluetooth.odex

# finishing up
log_print "un-mount the system partition"
umount $SYSTMP >> $LOG_FP 2>&1

exit 0