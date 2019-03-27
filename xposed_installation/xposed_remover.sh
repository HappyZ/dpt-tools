##########################################################################################
#
# Xposed framework uninstaller zip.
# Modified for DPT running in adb mode
#
# This script removes the Xposed framework files from the system partition.
# It doesn't touch the Xposed Installer app.
#
##########################################################################################

alias cat='busybox cat'
alias cut='busybox cut'
alias sed='busybox sed'
alias head='busybox head'
alias find='busybox find'
alias gunzip='busybox gunzip'


grep_prop() {
  REGEX="s/^$1=//p"
  shift
  FILES=$@
  if [ -z "$FILES" ]; then
    FILES=$PREFIX/system/build.prop
  fi
  cat $FILES 2>/dev/null | sed -n $REGEX | head -n 1
}

mv_perm() {
  mv -f $1 $2 || exit 1
  set_perm $2 $3 $4 $5 $6
}

set_perm() {
  chown $2:$3 $1 || exit 1
  chmod $4 $1 || exit 1
  if [ "$5" ]; then
    chcon $5 $1 2>/dev/null
  else
    chcon 'u:object_r:system_file:s0' $1 2>/dev/null
  fi
}

restore_link() {
  TARGET="${PREFIX}${1}"
  LINK_TARGET="${1}_xposed"
  XPOSED="${PREFIX}${1}_xposed"
  BACKUP="${PREFIX}${1}_original"
  # Don't touch $TARGET if the link was created by something else (e.g. SuperSU)
  if [ -f $BACKUP -a -L $TARGET -a "$(readlink $TARGET)" = $LINK_TARGET ]; then
    rm -f $TARGET
    mv_perm $BACKUP $TARGET $2 $3 $4 $5
  fi
  rm -f $XPOSED
}

restore_backup() {
  TARGET="${PREFIX}${1}"
  BACKUP="${PREFIX}${1}.orig"
  NO_ORIG="${PREFIX}${1}.no_orig"
  if [ -f $BACKUP ]; then
    mv_perm $BACKUP $TARGET $2 $3 $4 $5
    rm -f $NO_ORIG
  elif [ -f "${BACKUP}.gz" ]; then
    rm -f $TARGET $NO_ORIG
    gunzip "${BACKUP}.gz"
    mv_perm $BACKUP $TARGET $2 $3 $4 $5
  elif [ -f $NO_ORIG ]; then
    rm -f $TARGET $NO_ORIG
  fi
}

##########################################################################################

echo "************************************"
echo " Xposed Framework uninstaller zip"
echo "************************************"

echo "- Mounting /system and /vendor read-write"
# mount /system >/dev/null 2>&1
mount -o remount,rw /system
# mount /vendor >/dev/null 2>&1
# mount -o remount,rw /vendor >/dev/null 2>&1

PREFIX=
# if [ "$SYSTEM_ROOT_IMAGE" = "true" -a -f /twres/twrp -a -f /system/system/build.prop ]; then
#   # TWRP might mount the full system partion to /system, so files are actually in /system/system.
#   PREFIX=/system
# fi

# Check if build.prop is accessible now.
if [ ! -f $PREFIX/system/build.prop ]; then
  echo "! Failed: /system could not be mounted!"
  exit 1
fi

echo "- Checking environment"
API=$(grep_prop ro.build.version.sdk)
ABI=$(grep_prop ro.product.cpu.abi | cut -c-3)
ABI2=$(grep_prop ro.product.cpu.abi2 | cut -c-3)
ABILONG=$(grep_prop ro.product.cpu.abi)

ARCH=arm
IS64BIT=
if [ "$ABI" = "x86" ]; then ARCH=x86; fi;
if [ "$ABI2" = "x86" ]; then ARCH=x86; fi;
if [ "$API" -ge "21" ]; then
  if [ "$ABILONG" = "arm64-v8a" ]; then ARCH=arm64; IS64BIT=1; fi;
  if [ "$ABILONG" = "x86_64" ]; then ARCH=x64; IS64BIT=1; fi;
else
  echo "! This script doesn't work for SDK < 21 (yet)"
  exit 1
fi

# echo "DBG [$API] [$ABI] [$ABI2] [$ABILONG] [$ARCH]"

echo "- Restoring/removing files"
rm -f $PREFIX/system/xposed.prop
rm -f $PREFIX/system/framework/XposedBridge.jar

restore_link   /system/bin/app_process32               0 2000 0755 u:object_r:zygote_exec:s0
restore_backup /system/bin/dex2oat                     0 2000 0755 u:object_r:dex2oat_exec:s0
restore_backup /system/bin/dexdiag                     0 2000 0755
restore_backup /system/bin/dexlist                     0 2000 0755
restore_backup /system/bin/dexoptanalyzer              0 2000 0755 u:object_r:dexoptanalyzer_exec:s0
restore_backup /system/bin/oatdump                     0 2000 0755
restore_backup /system/bin/patchoat                    0 2000 0755 u:object_r:dex2oat_exec:s0
restore_backup /system/bin/profman                     0 2000 0755 u:object_r:profman_exec:s0

restore_backup /system/lib/libart.so                   0    0 0644
restore_backup /system/lib/libart-compiler.so          0    0 0644
restore_backup /system/lib/libart-dexlayout.so         0    0 0644
restore_backup /system/lib/libart-disassembler.so      0    0 0644
restore_backup /system/lib/libsigchain.so              0    0 0644
restore_backup /system/lib/libopenjdkjvm.so            0    0 0644
restore_backup /system/lib/libopenjdkjvmti.so          0    0 0644
rm -f $PREFIX/system/lib/libxposed_art.so
rm -f $PREFIX/system/lib/libxposed_art.so.no_orig

if [ "$API" -ge "22" -a "$API" -le "23" ]; then
  find $PREFIX/system $PREFIX/vendor -type f -name '*.odex.gz.xposed' 2>/dev/null | while read f; do mv "$f" "${f%.xposed}"; done
fi

echo "- Done"
echo " "
echo "************************************"
echo "It's recommended that you wipe the"
echo "Dalvik cache now."
echo "************************************"
echo " "

exit 0
