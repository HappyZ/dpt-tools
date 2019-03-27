##########################################################################################
#
# Xposed framework installer zip.
# Modified for DPT running in adb mode
#
# This script installs the Xposed framework files to the system partition.
# The Xposed Installer app is needed as well to manage the installed modules.
#
##########################################################################################

alias cat='busybox cat'
alias cut='busybox cut'
alias sed='busybox sed'
alias head='busybox head'
alias find='busybox find'


grep_prop() {
  REGEX="s/^$1=//p"
  shift
  FILES=$@
  if [ -z "$FILES" ]; then
    FILES='/system/build.prop'
  fi
  cat $FILES 2>/dev/null | sed -n $REGEX | head -n 1
}

android_version() {
  case $1 in
    15) echo '4.0 / SDK'$1;;
    16) echo '4.1 / SDK'$1;;
    17) echo '4.2 / SDK'$1;;
    18) echo '4.3 / SDK'$1;;
    19) echo '4.4 / SDK'$1;;
    21) echo '5.0 / SDK'$1;;
    22) echo '5.1 / SDK'$1;;
    23) echo '6.0 / SDK'$1;;
    24) echo '7.0 / SDK'$1;;
    25) echo '7.1 / SDK'$1;;
    26) echo '8.0 / SDK'$1;;
    27) echo '8.1 / SDK'$1;;
    *)  echo 'SDK'$1;;
  esac
}

cp_perm() {
  cp -f $1 $2 || exit 1
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

install_nobackup() {
  cp_perm ./$1 $1 $2 $3 $4 $5
}

install_and_link() {
  TARGET=$1
  XPOSED="${1}_xposed"
  BACKUP="${1}_original"
  if [ ! -f ./$XPOSED ]; then
    return
  fi
  cp_perm ./$XPOSED $XPOSED $2 $3 $4 $5
  # Don't touch $TARGET if the link was created by something else (e.g. SuperSU)
  if [ ! -f $BACKUP ]; then
    mv $TARGET $BACKUP || exit 1
    ln -s $XPOSED $TARGET || exit 1
    chcon -h 'u:object_r:system_file:s0' $TARGET 2>/dev/null
  fi
}

install_overwrite() {
  TARGET=$1
  if [ ! -f ./$TARGET ]; then
    return
  fi
  BACKUP="${1}.orig"
  NO_ORIG="${1}.no_orig"
  if [ ! -f $TARGET ]; then
    touch $NO_ORIG || exit 1
    set_perm $NO_ORIG 0 0 600
  elif [ -f $BACKUP ]; then
    rm -f $TARGET
    gzip $BACKUP || exit 1
    set_perm "${BACKUP}.gz" 0 0 600
  elif [ ! -f "${BACKUP}.gz" -a ! -f $NO_ORIG ]; then
    mv $TARGET $BACKUP || exit 1
    gzip $BACKUP || exit 1
    set_perm "${BACKUP}.gz" 0 0 600
  fi
  cp_perm ./$TARGET $TARGET $2 $3 $4 $5
}

##########################################################################################

echo "******************************"
echo "Xposed framework installer zip"
echo "******************************"

if [ ! -f "system/xposed.prop" ]; then
  echo "! Failed: Extracted file system/xposed.prop not found!"
  exit 1
fi

echo "- Mounting /system and /vendor read-write"
# mount /system >/dev/null 2>&1
# mount /vendor >/dev/null 2>&1
mount -o remount,rw /system
# mount -o remount,rw /vendor >/dev/null 2>&1
if [ ! -f '/system/build.prop' ]; then
  echo "! Failed: /system could not be mounted!"
  exit 1
fi

echo "- Checking environment"
API=$(grep_prop ro.build.version.sdk)
APINAME=$(android_version $API)
ABI=$(grep_prop ro.product.cpu.abi | cut -c-3)
ABI2=$(grep_prop ro.product.cpu.abi2 | cut -c-3)
ABILONG=$(grep_prop ro.product.cpu.abi)

XVERSION=$(grep_prop version system/xposed.prop)
XARCH=$(grep_prop arch system/xposed.prop)
XMINSDK=$(grep_prop minsdk system/xposed.prop)
XMAXSDK=$(grep_prop maxsdk system/xposed.prop)

XEXPECTEDSDK=$(android_version $XMINSDK)
if [ "$XMINSDK" != "$XMAXSDK" ]; then
  XEXPECTEDSDK=$XEXPECTEDSDK' - '$(android_version $XMAXSDK)
fi

ARCH=arm
IS64BIT=
if [ "$ABI" = "x86" ]; then ARCH=x86; fi;
if [ "$ABI2" = "x86" ]; then ARCH=x86; fi;
if [ "$API" -ge "21" ]; then
  if [ "$ABILONG" = "arm64-v8a" ]; then ARCH=arm64; IS64BIT=1; fi;
  if [ "$ABILONG" = "x86_64" ]; then ARCH=x64; IS64BIT=1; fi;
fi

# echo "DBG [$API] [$ABI] [$ABI2] [$ABILONG] [$ARCH] [$XARCH] [$XMINSDK] [$XMAXSDK] [$XVERSION]"

echo "  Xposed version: $XVERSION"

XVALID=
if [ "$ARCH" = "$XARCH" ]; then
  if [ "$API" -ge "$XMINSDK" ]; then
    if [ "$API" -le "$XMAXSDK" ]; then
      XVALID=1
    else
      echo "! Wrong Android version: $APINAME"
      echo "! This file is for: $XEXPECTEDSDK"
    fi
  else
    echo "! Wrong Android version: $APINAME"
    echo "! This file is for: $XEXPECTEDSDK"
  fi
else
  echo "! Wrong platform: $ARCH"
  echo "! This file is for: $XARCH"
fi

if [ -z $XVALID ]; then
  echo "! Please download the correct package"
  echo "! for your platform/ROM!"
  exit 1
fi

echo "- Placing files"
install_nobackup /system/xposed.prop                      0    0 0644
install_nobackup /system/framework/XposedBridge.jar       0    0 0644

install_and_link  /system/bin/app_process32               0 2000 0755 u:object_r:zygote_exec:s0
install_overwrite /system/bin/dex2oat                     0 2000 0755 u:object_r:dex2oat_exec:s0
install_overwrite /system/bin/oatdump                     0 2000 0755
install_overwrite /system/bin/patchoat                    0 2000 0755 u:object_r:dex2oat_exec:s0
install_overwrite /system/lib/libart.so                   0    0 0644
install_overwrite /system/lib/libart-compiler.so          0    0 0644
install_overwrite /system/lib/libart-disassembler.so      0    0 0644
install_overwrite /system/lib/libsigchain.so              0    0 0644
install_nobackup  /system/lib/libxposed_art.so            0    0 0644

if [ "$API" -ge "22" ]; then
  find /system /vendor -type f -name '*.odex.gz' 2>/dev/null | while read f; do mv "$f" "$f.xposed"; done
fi

echo "- Done"
exit 0
