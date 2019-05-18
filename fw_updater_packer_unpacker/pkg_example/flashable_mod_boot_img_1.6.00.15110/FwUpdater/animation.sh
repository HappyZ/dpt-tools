#!/bin/sh

epd_cmd()
{
  epd_fb_test $@ >/dev/null 2>&1
}

dispClear()
{
  epd_cmd gray DU PART 0
}

get_screen_resolution()
{
  head -1 /sys/class/graphics/fb0/modes | sed -e 's/^.*://' -e 's/p.*$//' -e 's/x/ /'
}

get_screen_width()
{
  set `get_screen_resolution`
  echo $1
}

get_screen_height()
{
  set `get_screen_resolution`
  echo $2
}

LOG_FP=$1

dispClear

while [ 1 ]
do
  for file in `\find $(dirname ${0})/images -name '*.bmp' | sort`; do
     epd_cmd file GC16 PART $file
     echo "[anim] displaying $file" >> $LOG_FP
     sleep 1
  done
done

exit 0
