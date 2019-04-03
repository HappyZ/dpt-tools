#!/bin/sh

UPDATER_BASE=$(dirname ${0})
${UPDATER_BASE}/eufwupdater.sh
# tentative exit
exit $?