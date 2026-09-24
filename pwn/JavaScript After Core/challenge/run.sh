#!/bin/sh
# Service entrypoint: read one JS program from the client, run it under the
# hardened jsc, then exit. win() runs ./readflag from this directory.
cd /home/ctf
tmp=$(mktemp /tmp/js.XXXXXX)
trap 'rm -f "$tmp"' EXIT
cat > "$tmp"
exec /jsc/bin/jsc "$tmp"
