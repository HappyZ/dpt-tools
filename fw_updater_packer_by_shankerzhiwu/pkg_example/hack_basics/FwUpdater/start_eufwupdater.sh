#!/bin/sh

# $1 update package
# $2 output directory
# $3 pub key to verify sig
# $4 pri key to decrypt data key

SIG_FILE="$2/sig.dat"
AES256_KEY="$2/aes256.key"
IV="$2/iv"

ANIM_SIG_FILE="$2/anim_sig.dat"
ANIM_PID=0


epd_cmd()
{
  epd_fb_test $@ >/dev/null 2>&1
}


########################################
# file header check
########################################
HEAD_MARK=`head -c 4 $1`
if [ $HEAD_MARK != "DPUP" ]
then
  echo "Invalid file"
  exit 0
fi


DATA_OFFSET=`dd if=$1 bs=4 skip=1 count=1 2>/dev/null | od -A n -t d4 -v`
BODY_SIZE=`dd if=$1 bs=4 skip=2 count=1 2>/dev/null | od -A n -t d4 -v`
########################################
# start animation for package check
########################################
ANIM_HEADER_OFFSET=$(( $DATA_OFFSET + $BODY_SIZE ))
if [ -z "$ANIM_HEADER_OFFSET" ]
then
  ANIM_HEADER_OFFSET=0
fi
ANIM_HEADER_SIZE=`dd if=$1 bs=1 skip=$ANIM_HEADER_OFFSET count=4 2>/dev/null | od -A n -t d4 -v`
if [ -z "$ANIM_HEADER_SIZE" ]
then
  ANIM_HEADER_SIZE=0
fi
ANIM_ARCH_SIZE=`dd if=$1 bs=1 skip=$(($ANIM_HEADER_OFFSET + 4)) count=4 2>/dev/null | od -A n -t d4 -v`
ANIM_SIG_SIZE=`dd if=$1 bs=1 skip=$(($ANIM_HEADER_OFFSET + 8)) count=4 2>/dev/null | od -A n -t d4 -v`
dd if=$1 of=$ANIM_SIG_FILE bs=1 skip=$(($ANIM_HEADER_OFFSET + 12)) count=$(($ANIM_SIG_SIZE)) 2>/dev/null
ANIM_ARCH_OFFSET=$(($ANIM_HEADER_OFFSET + $ANIM_HEADER_SIZE))
dd if=$1 bs=$ANIM_ARCH_OFFSET skip=1 2>/dev/null | head -c $(($ANIM_ARCH_SIZE)) | openssl dgst -sha256 -verify $3 -signature $ANIM_SIG_FILE 1>/dev/null
if [ $? -eq 0 ]
then
  start_prepare_animation.sh $1 $2 $ANIM_ARCH_OFFSET $(($ANIM_ARCH_SIZE)) &
  ANIM_PID=$!
fi



########################################
# extract sig
########################################
SIG_SIZE=`dd if=$1 bs=4 skip=4 count=1 2>/dev/null | od -A n -t d4 -v`
dd if=$1 of=$SIG_FILE bs=1 skip=20 count=$(($SIG_SIZE)) 2>/dev/null


########################################
# verify sig
########################################
# dd if=$1 bs=$(($DATA_OFFSET)) skip=1 2>/dev/null | head -c $(($BODY_SIZE)) | openssl dgst -sha256 -verify $3 -signature $SIG_FILE 1>/dev/null
#if [ $? -ne 0 ]
#then
#  echo "Verify failed."
#  exit 0
#fi


########################################
# decrypt data key
########################################
ENC_KEY_OFFSET=$((20 + $SIG_SIZE))
PAD_SIZE=$((16 - $SIG_SIZE % 16 ))
if [ $PAD_SIZE -ne 16 ]
then
  ENC_KEY_OFFSET=$(( $ENC_KEY_OFFSET + $PAD_SIZE ))
fi

ENC_KEY_SIZE=`dd if=$1 bs=1 skip=${ENC_KEY_OFFSET} count=4 2>/dev/null | od -A n -t d4 -v`
ENC_KEY_OFFSET=$(( $ENC_KEY_OFFSET + 4 ))
dd if=$1 bs=1 skip=${ENC_KEY_OFFSET} count=$(($ENC_KEY_SIZE)) 2>/dev/null | openssl rsautl -decrypt -inkey $4 > ${AES256_KEY}


########################################
# extract iv
########################################
IV_OFFSET=$(($ENC_KEY_OFFSET + $ENC_KEY_SIZE))
dd if=$1 of=$IV bs=1 skip=${IV_OFFSET} count=32 2>/dev/null


########################################
# decrypt data and extract directory tree
########################################
dd if=$1 bs=$(($DATA_OFFSET)) skip=1 2>/dev/null | head -c $(($BODY_SIZE)) | openssl enc -d -aes-256-cbc -K `cat ${AES256_KEY}` -iv `cat ${IV}` | tar -xz -C $2


########################################
# stop animation for package check
########################################
if [ $ANIM_PID -ne 0 ]
then
  kill $ANIM_PID
  epd_cmd gray DU PART 0
  epd_cmd wait 300000
fi


########################################
# start updater
########################################
if [ -f ${2}/FwUpdater/eufwupdater.sh ]
then
  ${2}/FwUpdater/eufwupdater.sh
  exit $?	# tentative
else
  echo "Invalid archive (No updater script)."
  exit 0
fi
