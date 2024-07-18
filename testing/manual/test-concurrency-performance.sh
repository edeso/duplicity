#!/usr/bin/env bash

export PASSPHRASE=test

transfer_times=(0 500 1000 10000 30000 60000)
concurrency=(1 2 5 8)
transfer_times=(0 500 1000 2500)
concurrency=(1 2 5)
ts=$(date +"%Y%m%d-%H%M%S")
dst_dir=/tmp/back-cc-test
result_dir=/tmp/results-${ts}
mkdir -p $result_dir

for tt in "${transfer_times[@]}"; do
    for cc in "${concurrency[@]}"; do 
    (
        rm -rf ${dst_dir}
        variance=$(( tt * 10 / 100 ))
        effective_delay=$(( tt / 3  )) # delay takes place three times
        echo "tt: ${tt}, effective_delay: ${effective_delay}, variance: ${variance}, cc: ${cc}"
        DUP_FAIL_DELAY_FIX_MS=${effective_delay} DUP_FAIL_DELAY_RANDOM_MS=${variance} PYTHONPATH=. python duplicity/__main__.py full --jsonstat --num-ret=2 --backend-ret=3 --encrypt-key=839E6A2856538CCF --volsize 2 --verbosity d --concurrency ${cc} /workspaces/duplicity/tmp/hugefile/video.mp4 --archive-dir /tmp/back.meta fortestsonly://${dst_dir}
        gpg --batch --passphrase ${PASSPHRASE} --pinentry-mode loopback -d ${dst_dir}/duplicity-full.*.jsonstat.gpg > ${result_dir}/jsonstat-tt${tt}-cc${cc}.json
     ) &> ${result_dir}/run-tt${tt}-cc${cc}.log
    done
done