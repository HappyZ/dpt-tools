device=/dev/zero
result=NG


destructor ()
{
  echo $result
}
trap destructor 0 2 11 15


case $1 in

normal)
  ;;

recovery)
  device=/dev/urandom
  ;;

*)
  exit 1
  ;;

esac


if rawdata --set_dump=boot_mode < $device; then
  result=OK
fi
