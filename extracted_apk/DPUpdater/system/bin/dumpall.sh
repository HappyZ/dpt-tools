#!/system/bin/sh
if [ -e "/sdcard/dmesg" ]
then
    rm /sdcard/dmesg
fi
if [ -e "/sdcard/dumpsys" ]
then
    rm /sdcard/dumpsys
fi

chmod 666 /sys/fs/pstore/*

dmesg > /sdcard/dmesg
dumpsys > /sdcard/dumpsys
