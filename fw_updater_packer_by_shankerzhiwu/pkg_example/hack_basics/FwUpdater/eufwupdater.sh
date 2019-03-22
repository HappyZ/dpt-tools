#!/bin/sh

LOG_FP="/root/updater_$(date +%s).log"
exec &>"$LOG_FP"

UPDATER_BASE=$(dirname ${0})
cd "$UPDATER_BASE"

###
### Initialize printing on screen service
###

YAFT_PID=0
./yaft </dev/null >/tmp/pty.txt &
YAFT_PID=$!
pty=""
for i in $(seq 1 10); do
  pty="$(cat /tmp/pty.txt)"
  if [ -n "$pty" ]; then
    break;
  fi
  sleep 1
done

if [ -z "$pty" ]; then
  echo "openpty failed"
  kill -INT $YAFT_PID
  exit 0;
fi

echo "will open pty $pty"
rm "/tmp/_fifo"
mkfifo "/tmp/_fifo"
tee "$pty" < /tmp/_fifo &

exec &>"/tmp/_fifo"

###
### Starting message
###
cat LICENSE

./greetings.sh


###
### Start the process
###
./startprocess.sh


###
### Ending message
###
./finished.sh

for i in $(seq 5 -1 1); do
	echo "Reboot in ${i} seconds."
	sleep 1
done


exit 0
