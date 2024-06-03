#!/bin/bash


trap "echo Exit detected." EXIT

cd `dirname $0`/../..

export PYTHONPATH=`pwd`

rm -rf /tmp/issue745 ~/.cache/duplicity/issue745

ARGS="--no-enc --no-com --vol=1 --num-ret=2 --backend-ret=3
      --async --name=issue745 --log-timestamp -v=d
      /bin fortestsonly:///tmp/issue745"
echo "Common args:" ${ARGS}

# export PYDEVD=vscode
export DUP_FAIL_WITH_EXCEPTION=vol2.difftar
bin/duplicity full ${ARGS} &
PID=$!
sleep 15
if ps -p ${PID} > /dev/null; then
    echo
    echo "Test failed. Task is hung.  Killing."
    pkill -P ${PID}
    echo "Removing failed task lockfile"
    rm -f ~/.cache/duplicity/issue745/lockfile
    echo
fi
ls -lh /tmp/issue745 ~/.cache/duplicity/issue745

# echo "Press ENTER to check if 2nd full run will recover."
# read
# bin/duplicity full ${ARGS}
# ls -lh /tmp/issue745 ~/.cache/duplicity/issue745
