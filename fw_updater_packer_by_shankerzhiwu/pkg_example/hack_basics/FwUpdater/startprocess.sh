#!/bin/sh

ROOTPWD=/etc/passwd
DIAGFUNC=/usr/local/bin/diag_functions
UPDATER=/usr/local/bin/updater_check.sh
FWUPDATER=/usr/local/bin/start_eufwupdater.sh
KEY_DETECTION_TMPF=/tmp/key_pressed.log


###
### key detection function
###
detect_key_pressed () {
    echo "---- Waiting for key pressing (${1}s count down)..."
    tmpcontent=""
    for i in $(seq ${1} -1 1)
    do
        echo "---- Waiting for response for ${i} seconds.."
        tmpcontent="$(busybox script -c 'timeout -t 1 keyscan' -f -q ${KEY_DETECTION_TMPF})"
        echo $tmpcontent | grep -Fq "HOME"
        if [ $? -eq 0 ]
        then
            echo "---- found HOME!"
            return 1
        fi
        echo $tmpcontent | grep -Fq "POWER"
        if [ $? -eq 0 ]
        then
            echo "----found POWER!"
            return 2
        fi
    done
    return 0
}


echo ""
echo "================================================"
echo " Replacing diagnosis root password to 12345.."
echo "================================================"
if [ ! -f ${ROOTPWD} ]
then
    echo "!! Error: Cannot find ${ROOTPWD}, exiting.."
    exit 0
fi
echo "== Original ${ROOTPWD}:"
cat ${ROOTPWD}
echo "== Backing up..."
cp ${ROOTPWD} ${ROOTPWD}_bak
echo "== Replacing..."
# sed in place
sed -i '/root:/c\root:$6$i2VmFAOV$sEMLa5no1zFKnEpFdobNI2dJFqGZE3sWUFJDf1Jn34vO8\.Q9EuwP5\.7aGpmwNLsyX\/lOrh285\.xSzjSHNzMau0:0:0::\/root:\/bin\/sh' $ROOTPWD
echo "== New ${ROOTPWD}:"
cat ${ROOTPWD}

# validation
echo "== Looking fine?"
echo "==== If YES, do nothing, or press HOME to continue (default)..."
echo "==== If NO, press POWER to rollback..."
detect_key_pressed 30
status=$?
if [ $status -eq 2 ]
then
    echo "== Rolling back..."
    # use cat to prevent permission change
    cat ${ROOTPWD}_bak > ${ROOTPWD}
    echo "== Current ${ROOTPWD}:"
    cat ${ROOTPWD}
    echo "== Done. No modifications were made."
    exit 0
fi


echo ""
echo "========================================="
echo " Enabling diagnosis mode without OTG.."
echo "========================================="
echo ""
echo "== Original ${DIAGFUNC} (30 lines):"
head -n 30 ${DIAGFUNC}
echo "== Backing up..."
cp ${DIAGFUNC} ${DIAGFUNC}_bak
echo "== Enabling..."
# use cat to prevent permission change
cat diag_functions > ${DIAGFUNC}
echo "== New ${DIAGFUNC} (30 lines):"
head -n 30 ${DIAGFUNC}

# validation
echo "== Looking fine?"
echo "==== If YES, do nothing, or press HOME to continue (default)..."
echo "==== If NO, press POWER to rollback..."
detect_key_pressed 30
status=$?
if [ $status -eq 2 ]
then
    echo "== Rolling back..."
    # use cat to prevent permission change
    cat ${DIAGFUNC}_bak > ${DIAGFUNC}
    echo "== Current ${DIAGFUNC} (30 lines):"
    head -n 30 ${DIAGFUNC}
    echo "== Done. No modifications were made."
    exit 0
fi


echo ""
echo "======================================="
echo " Patching customized updater script.."
echo "======================================="
echo ""

echo "== Original ${UPDATER} (30 lines):"
tail -n 30 ${UPDATER}
echo "== Backing up..."
cp ${UPDATER} ${UPDATER}_bak
echo "== Enabling..."
# use cat to prevent permission change
cat updater_check.sh > ${UPDATER}
echo "== New ${UPDATER} (30 lines):"
tail -n 30 ${UPDATER}

echo "== Original ${FWUPDATER} (30 lines):"
tail -n 30 ${FWUPDATER}
echo "== Backing up..."
cp ${FWUPDATER} ${FWUPDATER}_bak
echo "== Enabling..."
# use cat to prevent permission change
cat start_eufwupdater.sh > ${FWUPDATER}
echo "== New ${FWUPDATER} (30 lines):"
tail -n 30 ${FWUPDATER}

# validation
echo "== Looking fine?"
echo "==== If YES, do nothing, or press HOME to continue (default)..."
echo "==== If NO, press POWER to rollback..."
detect_key_pressed 30
status=$?
if [ $status -eq 2 ]
then
    echo "== Rolling back..."
    # use cat to prevent permission change
    cat ${UPDATER}_bak > ${UPDATER}
    cat ${FWUPDATER}_bak > ${FWUPDATER}
    echo "== Current ${UPDATER} (30 lines):"
    tail -n 30 ${UPDATER}
    echo "== Current ${FWUPDATER} (30 lines):"
    tail -n 30 ${FWUPDATER}
    echo "== Done. No modifications were made."
    exit 0
fi



