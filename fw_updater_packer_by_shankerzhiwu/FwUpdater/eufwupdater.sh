#!/bin/sh

LOG_FP="/root/updater_$(date +%s).log"
exec &>"$LOG_FP"

UPDATER_BASE=$(dirname ${0})
cd "$UPDATER_BASE"

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

echo "success"
echo "This is a demo update package which does nothing."
echo "enjoy"

for i in $(seq 10 -1 1); do
  echo "will done in ${i} seconds."
  sleep 1
done

exit 0
