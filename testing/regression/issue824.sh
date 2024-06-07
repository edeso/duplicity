#!/bin/sh

TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/testfiles"

for i in $(seq 1 10); do
    dd if=/dev/urandom of="$TMPDIR/testfiles/$i.bin" bs=1M count=50
done
PASSPHRASE=foo duplicity "$TMPDIR/testfiles" "file://$TMPDIR/testbackup"
TOCORRUPT=$(echo $TMPDIR/testbackup/*vol2*gpg)
mv "$TOCORRUPT" "$TMPDIR/testbackup/GOOD"
head -c -1000000 "$TMPDIR/testbackup/GOOD" > "$TOCORRUPT"
PASSPHRASE=foo duplicity --ignore-errors --num-retries 1 "file://$TMPDIR/testbackup" "$TMPDIR/testrestore"
if ! test -f "$TMPDIR/testrestore/9.bin"; then
    >2 echo "Restore failed to ignore errors"
    rm -rf $TMPDIR
    exit 1
fi
rm -rf $TMPDIR
