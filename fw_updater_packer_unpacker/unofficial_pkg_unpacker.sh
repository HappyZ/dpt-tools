#!/bin/sh

# Unpacker for DPT pkg
# HappyZ
# Thanks to anonymous contributer somewhere on earth

# PKG FILE FORMAT
# byte 1--4:          DPUP - file recognizer
# byte 5--8:          data offset location A
# byte 9--12:         total data content size D
# byte 13--16:        nothing
# byte 17--20:        sigfile size B
# byte 21--(20+B):    sigfile data
# byte (21+(-B%16)%16)--(25+(-B%16)%16):  encrypted data aes key size (BE) C
# byte (+1)--(+C):    encrypted data aes key bytes
# byte (+1)--(+32):   initial vector  --- up till now bytes shall equal to A
# byte (A+1)--(A+D):  encrypted data
# byte (+1)--(+4):    animation header size E
# byte (+1)--(+4):    animation data size F
# byte (+1)--(+4):    animation sigfile size G
# byte (+1)--(+(-G%16)%16): animation sigfile --- here bytes shall be A+D+E
# byte (A+D+E+1)--(A+D+E+F): animation data

# zipped data format
# FwUpdater
# |- boot.img
# |- boot.img.md5
# |- system.img
# |- system.img.md5
# |- eufwupdater.sh
# |- ...


# params
PKGFILE=$1  # pkg file
OUTDIR=$2  # output folder
SHA256KEY="./key.pub"
DATAKEY_D="./key.private"

# predefined outputs
SIGFILE="$OUTDIR/signature"
AESFILE="$OUTDIR/aes.key"
IVFILE="$OUTDIR/init_vector"
SIGFILE_ANIM="$OUTDIR/signature_animation"

# commands
ODUMP="od -A n -t d4 -v"


# check if output folder does not exist, make one
if [[ ! -d $OUTDIR ]]; then
  mkdir $OUTDIR;
fi
if [[ ! -d $OUTDIR ]]; then  # check again
  echo "! Err: looks like we cannot create this folder"
  exit 0
fi

echo "* file header check.."
if [ $(head -c 4 $PKGFILE) != "DPUP" ]; then
  echo "! Err: this seems to be an invalid pkg"
  exit 0
fi

echo "* getting data block size"
OFFSET_DATA=`dd if=$PKGFILE bs=4 skip=1 count=1 2>/dev/null | $ODUMP`
DATA_SIZE=`dd if=$PKGFILE bs=4 skip=2 count=1 2>/dev/null | $ODUMP`

echo "* extract signature.."
SIG_SIZE=`dd if=$PKGFILE bs=4 skip=4 count=1 2>/dev/null | $ODUMP`
dd if=$PKGFILE of=$SIGFILE bs=1 skip=20 count=$((SIG_SIZE)) 2>/dev/null

echo "* verify data with signature.."
dd if=$PKGFILE bs=$((OFFSET_DATA)) skip=1 2>/dev/null | head -c $((DATA_SIZE)) | openssl dgst -sha256 -verify $SHA256KEY -signature $SIGFILE 1>/dev/null
# if [ $? -ne 0 ]; then
#   echo "! Err: failed to verify data with provided signature"
#   exit 0
# fi

echo "* get encrypted data aes key.."
OFFSET_DATAKEY_E=$((20 + SIG_SIZE + ((-(SIG_SIZE % 16)) % 16)))
DATAKEY_E_SIZE=`dd if=$PKGFILE bs=1 skip=$OFFSET_DATAKEY_E count=4 2>/dev/null | $ODUMP`
OFFSET_DATAKEY_E=$((OFFSET_DATAKEY_E + 4))
echo "** decrypt it via $DATAKEY_D"
dd if=$PKGFILE bs=1 skip=$OFFSET_DATAKEY_E count=$((DATAKEY_E_SIZE)) 2>/dev/null | openssl rsautl -decrypt -inkey $DATAKEY_D > $AESFILE

echo "* extract 32-byte initial vector.."
OFFSET_IV=$((OFFSET_DATAKEY_E + DATAKEY_E_SIZE))
dd if=$PKGFILE of=$IVFILE bs=1 skip=$OFFSET_IV count=32 2>/dev/null

echo "* decrypt data to zipped tar.."
dd if=$PKGFILE bs=$((OFFSET_DATA)) skip=1 2>/dev/null | head -c $((DATA_SIZE)) | openssl enc -d -aes-256-cbc -K `cat $AESFILE` -iv `cat $IVFILE` > $OUTDIR/decrypted_pkg.tar.gz

echo "* unzip data.."
tar -xzf $OUTDIR/decrypted_pkg.tar.gz -C $OUTDIR

echo "* checking if animation data followed by.."
OFFSET_ANIM_HEADER=$((OFFSET_DATA + DATA_SIZE))
ANIM_HEADER_SIZE=`dd if=$PKGFILE bs=1 skip=$OFFSET_ANIM_HEADER count=4 2>/dev/null | $ODUMP`
if [ -z "$ANIM_HEADER_SIZE" ]; then
  ANIM_HEADER_SIZE=0
fi
if [[ $((ANIM_HEADER_SIZE)) -gt 0 ]]; then
  echo "** found animation block, getting animation data size.."
  ANIM_DATA_SIZE=`dd if=$PKGFILE bs=1 skip=$((OFFSET_ANIM_HEADER + 4)) count=4 2>/dev/null | $ODUMP`

  echo "** get animation signature.."
  ANIM_SIG_SIZE=`dd if=$PKGFILE bs=1 skip=$((OFFSET_ANIM_HEADER + 8)) count=4 2>/dev/null | $ODUMP`
  dd if=$PKGFILE of=$SIGFILE_ANIM bs=1 skip=$((OFFSET_ANIM_HEADER + 12)) count=$(($ANIM_SIG_SIZE)) 2>/dev/null

  echo "** verify animation data with signature.."
  OFFSET_ANIM_DATA=$((OFFSET_ANIM_HEADER + ANIM_HEADER_SIZE))
  dd if=$PKGFILE bs=$((OFFSET_ANIM_DATA)) skip=1 2>/dev/null | head -c $((ANIM_DATA_SIZE)) | openssl dgst -sha256 -verify $SHA256KEY -signature $SIGFILE_ANIM
  if [ $? -ne 0 ]; then
    echo "! Err: failed to verify animation data with provided signature"
    exit 0
  fi

  echo "** dump animation data to zipped tar.."
  dd if=$PKGFILE bs=$((OFFSET_ANIM_DATA)) skip=1 2>/dev/null > $OUTDIR/decrypted_animation_pkg.tar.gz

  echo "** unzip the tar.."
  tar -xzf $OUTDIR/decrypted_animation_pkg.tar.gz -C $OUTDIR
fi

