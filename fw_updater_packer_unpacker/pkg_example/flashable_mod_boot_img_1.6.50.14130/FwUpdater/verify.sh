#!/bin/sh

sync
echo 3 > /proc/sys/vm/drop_caches

LOG_FP=$2

BOOT_IMG_SIZE=`stat -c%s $1/boot-1.6.50.14130-mod-200405-233932.img`

BLK8_MD5=`dd if=/dev/mmcblk0p8 bs=$BOOT_IMG_SIZE count=1 | md5sum | cut -d " " -f1`

BOOT_MD5=`cat $1/boot-1.6.50.14130-mod-200405-233932.img.md5`

echo "BLK08=$BLK8_MD5" >> $LOG_FP
echo " BOOT=$BOOT_MD5" >> $LOG_FP


if [ $BLK8_MD5 = $BOOT_MD5 ];
then
echo "Verify OK" >> $LOG_FP
exit 0;
fi
echo "Verify NG" >> $LOG_FP
exit 127;


