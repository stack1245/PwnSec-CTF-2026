#!/bin/sh
# Container entrypoint. FLAG (and DOMAIN) exist only at runtime, never during
# docker build, so this is the one place the flag reaches the filesystem.
#
# win() runs ./readflag with cwd = /home/ctf (run.sh cds there) and readflag
# opens "flag.txt" relative to that cwd, so the flag must land at
# /home/ctf/flag.txt under exactly that name.
set -eu

: "${FLAG:?FLAG is required}"

rm -f /home/ctf/flag.txt
umask 077
printf '%s\n' "$FLAG" > /home/ctf/flag.txt
chmod 0400 /home/ctf/flag.txt

# Drop the flag from the environment: a half-working exploit should not be able
# to read it out of /proc/self/environ. Reaching it now needs the win() gate or
# full code execution inside the jsc process.
unset FLAG

exec socat TCP-LISTEN:1337,reuseaddr,fork EXEC:/home/ctf/run.sh,stderr
