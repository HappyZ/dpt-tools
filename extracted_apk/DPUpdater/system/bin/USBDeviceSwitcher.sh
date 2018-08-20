#!/system/bin/sh

SERIAL_COMF_COM="busybox stty -F /dev/ttyGS0"
IFUP_RETRY=5
IFUP_IVAL=500000


if test $1 == "serial_conf_setup"
then
     ${SERIAL_COMF_COM} raw
fi

if test $1 == "serial_conf_recover"
then
    ${SERIAL_COMF_COM} -raw
fi

if test $1 == "ifup"
then
    IF_NAME=${2}0

    busybox usleep ${IFUP_IVAL}

    for I in `busybox seq ${IFUP_RETRY}`
    do

        busybox usleep ${IFUP_IVAL}

        busybox ifconfig ${IF_NAME} up

        if test $? -eq 0
        then
            break
        fi

        if test ${I} -eq ${IFUP_RETRY}
        then
            exit -1
        fi

    done

    ip -6 route add fe80::/64 dev ${IF_NAME} metric 256 table local
fi

