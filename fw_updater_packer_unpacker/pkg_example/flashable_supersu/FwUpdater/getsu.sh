#!/bin/sh

# initialization
UPDATER_BASE=$(dirname ${0})
TAG="[getsu.sh]"
LOG_FP=$1

SU=${UPDATER_BASE}/sudo/su
SUPOLICY=${UPDATER_BASE}/sudo/supolicy
LIBSUPOL_SO=${UPDATER_BASE}/sudo/libsupol.so
INSTALL_RECOVERY=${UPDATER_BASE}/sudo/install-recovery.sh

SYSTMP=${UPDATER_BASE}/systmp
SYSXBIN=${SYSTMP}/xbin
SYSSBIN=${SYSTMP}/sbin
SYSBIN=${SYSTMP}/bin
SYSLIB=${SYSTMP}/lib
SYSETC=${SYSTMP}/etc
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

ln_silent() {
  log_print "creat static link file $2 pointing to $1"
  ln -s $1 $2 1>/dev/null 2>/dev/null
}

# check file existence
if ! [ -f $SU -a -f $SUPOLICY -a -f $LIBSUPOL_SO -a -f $INSTALL_RECOVERY ]
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

# remove old files
log_print "removing old files.."
rm -f ${SYSBIN}/su
rm -f ${SYSXBIN}/su
rm -f ${SYSSBIN}/su

# add new files
log_print "creating new files.."
mkdir -p ${SYSBIN}/.ext
set_perm 0 0 0777 ${SYSBIN}/.ext
cp_perm 0 0 0755 $SU ${SYSBIN}/.ext/.su
cp_perm 0 0 0755 $SU ${SYSXBIN}/su
cp_perm 0 0 0755 $SU ${SYSXBIN}/daemonsu
cp_perm 0 0 0755 $SUPOLICY ${SYSXBIN}/supolicy
cp_perm 0 0 0644 $LIBSUPOL_SO ${SYSLIB}/libsupol.so
cp_perm 0 0 0755 $INSTALL_RECOVERY ${SYSBIN}/install-recovery.sh

log_print "remove ${SYSBIN}/app_process.."
rm -f ${SYSBIN}/app_process
ln_silent "/system/xbin/daemonsu" ${SYSBIN}/app_process

if [ ! -f "${SYSBIN}/app_process32_original" ]
then
  log_print "backing up app_process32 to app_process32_original.."
  mv ${SYSBIN}/app_process32 ${SYSBIN}/app_process32_original
else
  log_print "app_process32_original already exists.."
  rm -f ${SYSBIN}/app_process32
fi

ln_silent "/system/xbin/daemonsu" ${SYSBIN}/app_process32
if [ ! -f "${SYSBIN}/app_process_init" ]
then
  cp_perm 0 2000 0755 ${SYSBIN}/app_process32_original ${SYSBIN}/app_process_init
else
  log_print "app_process_init already exists"
fi
echo 1 > ${SYSETC}/.installed_su_daemon
set_perm 0 0 0644 ${SYSETC}/.installed_su_daemon

# finishing up
umount $SYSTMP >> $LOG_FP 2>&1

exit 0