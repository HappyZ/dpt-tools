#!/bin/sh

# Repacker for DPT pkg
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

# we do not care about animation

# correct repacking behavior for MacOS
export COPYFILE_DISABLE=true

# params
INDIR=$1  # input folder
TMPDIR=$INDIR
PKGFILE=$1/FwUpdater.pkg  # output pkg file
SHA256KEY="./key.pub"
SIGKEY="./key.private"  # we use data encryption key (ignored anyway)
DATAKEY_D="./key.private"



# predefined outputs
SIGFILE="$INDIR/signature"
AESFILE="$INDIR/aes.key"
IVFILE="$INDIR/init_vector"
SIGFILE_ANIM="$INDIR/signature_animation"

# check if input folder exists
if [[ ! -d $INDIR ]]; then
  echo "! Err: input folder does not exist"
  exit 0
fi

echo "* zip data.."
CUR_DIR=$(pwd)
cd $INDIR && tar -czf repacked_pkg.tar.gz FwUpdater/ && cd $CUR_DIR

echo "* encrypt zipped tar"
openssl enc -e -aes-256-cbc -K `cat $AESFILE` -iv `cat $IVFILE` -in $INDIR/repacked_pkg.tar.gz -out $TMPDIR/tmp.step1
OFFSET_DATA=0
DATA_SIZE=$(wc -c < $TMPDIR/tmp.step1)

echo "* add 32-byte initial vector"
cat $IVFILE $TMPDIR/tmp.step1 > $TMPDIR/tmp.step2
OFFSET_DATA=$((OFFSET_DATA + 32))

echo "* encrypt the aes key with our private $DATAKEY_D"
openssl rsautl -encrypt -inkey $DATAKEY_D -in $AESFILE -out $TMPDIR/tmp.step3.1
DATAKEY_E_SIZE=$(wc -c < $TMPDIR/tmp.step3.1)
cat $TMPDIR/tmp.step3.1 $TMPDIR/tmp.step2 > $TMPDIR/tmp.step3.2
printf "%.8x" $((DATAKEY_E_SIZE)) | sed -E 's/(..)(..)(..)(..)/\4\3\2\1/' | xxd -r -p | cat - $TMPDIR/tmp.step3.2 > $TMPDIR/tmp.step3
OFFSET_DATA=$((OFFSET_DATA + DATAKEY_E_SIZE + 4))

echo "* sign w/ private key $SIGKEY"
openssl dgst -sha256 -sign $SIGKEY -out $TMPDIR/tmp.step4.1 $TMPDIR/tmp.step1
openssl dgst -sha256 -verify $SHA256KEY -signature $TMPDIR/tmp.step4.1 $TMPDIR/tmp.step1
if [ $? -ne 0 ]; then
  echo "! Warning: failed to verify sha256 - highly likely $SIGKEY is not an nofficial one. Ignore this and proceed."
  # exit 0
fi
SIG_SIZE=$(wc -c < $TMPDIR/tmp.step4.1)
if [ $(((-(SIG_SIZE % 16)) % 16)) -gt 0 ]; then
  echo "! Err: not supported for SIG_SIZE not mutiple of 16"
  exit -1
fi
cat $TMPDIR/tmp.step4.1 $TMPDIR/tmp.step3 > $TMPDIR/tmp.step4.2
printf "%.8x" $((SIG_SIZE)) | sed -E 's/(..)(..)(..)(..)/\4\3\2\1/' | xxd -r -p | cat - $TMPDIR/tmp.step4.2 > $TMPDIR/tmp.step4
OFFSET_DATA=$((OFFSET_DATA + SIG_SIZE + 4))

echo "* assign data block size and offset"
printf "%.8x" 0 | sed -E 's/(..)(..)(..)(..)/\4\3\2\1/' | xxd -r -p | cat - $TMPDIR/tmp.step4 > $TMPDIR/tmp.step5.1
printf "%.8x" $((DATA_SIZE)) | sed -E 's/(..)(..)(..)(..)/\4\3\2\1/' | xxd -r -p | cat - $TMPDIR/tmp.step5.1 > $TMPDIR/tmp.step5.2
OFFSET_DATA=$((OFFSET_DATA + 4 + 4 + 4 + 4))

echo "OFFSET_DATA: $OFFSET_DATA, DATA_SIZE: $DATA_SIZE"

printf "%.8x" $((OFFSET_DATA)) | sed -E 's/(..)(..)(..)(..)/\4\3\2\1/' | xxd -r -p | cat - $TMPDIR/tmp.step5.2 > $TMPDIR/tmp.step5

echo "* add file header"
printf "DPUP" | cat - $TMPDIR/tmp.step5 > $PKGFILE

# remove tmp files
rm $TMPDIR/tmp.step*
rm $INDIR/repacked_pkg.tar.gz
