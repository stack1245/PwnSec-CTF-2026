# syntax=docker/dockerfile:1
#
# JavaScript After Core -- hardened WebKit jsc served as a TCP service.
#
# Builds JavaScriptCore at the pinned pre-fix revision (see REVISION / TAG) for
# linux/amd64, applies diff.patch (shell hardening + the win() gate), and serves
# it behind socat: a client sends one JS program, it runs once, the connection
# closes. If the program satisfies win() -- mutate the immutable string
# hello!!! -> pwned!!! -> world!!! -- the server runs ./readflag.
#
# The image ships ONLY jsc + readflag behind socat. No solver, no flag baked in:
# the platform injects FLAG at runtime and entrypoint.sh writes it to flag.txt.
#
# Build (about 40-90 min on 8 cores; the WebKit checkout is ~16 GB):
#   docker build -t ctfae:javascript-after-core .
#   docker build --build-arg PARALLEL=8 -t ctfae:javascript-after-core .
#
# Run:
#   docker run -d --rm -p 1337:1337 -e FLAG=pwnsec{test} ctfae:javascript-after-core
#   nc -N localhost 1337 < exploit.js
#
# Notes:
#  - .dockerignore MUST keep WebKit out of the build context -- Docker uploads the
#    whole context dir regardless of which files COPY references.
#  - PARALLEL (default 4) caps -j; the JSCOnly build.sh otherwise forces -j<ncpu>.
#    Compiling JSC's biggest unified TUs is memory-heavy -- on <16 GB machines lower
#    it (--build-arg PARALLEL=2) or raise Docker's memory limit to avoid OOM "Killed".
#  - The reference solver's HDR_DOUBLE/HDR_CONTIG are calibrated for this exact
#    image (pinned revision + ubuntu:24.04 + clang). Re-derive them if the base
#    image or toolchain changes.
#  - amd64 only: the exploit constants are x86-64 specific, and Fargate runs amd64.

############################
# Stage 1: build jsc + readflag
############################
FROM --platform=linux/amd64 ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517 AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential clang cmake ninja-build git \
        python3 perl ruby pkg-config ca-certificates \
        libglib2.0-dev libtasn1-6-dev libicu-dev libxml2-dev \
        libsqlite3-dev libxslt1-dev libfontconfig1-dev libfreetype6-dev \
        libpng-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

ENV CC=clang CXX=clang++

WORKDIR /wk

# Shallow-fetch the exact pinned WebKit revision (cached after first build).
# Keep in sync with the REVISION file next to this Dockerfile.
ARG WEBKIT_REF=f1c8d9a5a1c38aa3badcf7b8ffb6b19e88b50001
RUN for i in 1 2 3 4 5; do \
        git init webkit && cd webkit \
        && git remote add origin https://github.com/WebKit/WebKit.git \
        && git fetch --depth 1 origin ${WEBKIT_REF} \
        && git checkout FETCH_HEAD \
        && break \
        || { cd /wk && rm -rf webkit; sleep 10; }; \
    done && test -d /wk/webkit/.git

# Standard JSCOnly Release build. PARALLEL caps -j (the JSCOnly build.sh otherwise
# forces -j<ncpu> and can OOM a small VM). The WebKitBuild dir is a cache mount so
# rebuilds are incremental.
ARG PARALLEL=4
COPY diff.patch /wk/
RUN --mount=type=cache,target=/wk/webkit/WebKitBuild \
    cd webkit \
    && git apply /wk/diff.patch \
    && ./Tools/Scripts/build-jsc --jsc-only --release --makeargs="-j${PARALLEL}" \
    && cp -a WebKitBuild/JSCOnly/Release /jsc

COPY readflag.c /wk/
RUN gcc -o /jsc/readflag /wk/readflag.c

###########################
# Stage 2: minimal runtime
###########################
FROM --platform=linux/amd64 ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517 AS runtime
ENV DEBIAN_FRONTEND=noninteractive
# netcat-openbsd is only used by the healthcheck probe.
RUN apt-get update && apt-get install -y --no-install-recommends \
        socat netcat-openbsd libatomic1 libglib2.0-0 libicu74 libtasn1-6 \
        libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m ctf

COPY --from=builder /jsc /jsc
ENV LD_LIBRARY_PATH=/jsc/lib:/jsc

WORKDIR /home/ctf
COPY run.sh entrypoint.sh /home/ctf/
COPY --from=builder /jsc/readflag /home/ctf/readflag
RUN chmod 0755 /home/ctf/run.sh /home/ctf/entrypoint.sh /home/ctf/readflag \
    && chown -R ctf:ctf /home/ctf

USER ctf
EXPOSE 1337
# FLAG is injected at runtime, never at build time -- entrypoint.sh places it.
ENTRYPOINT ["/home/ctf/entrypoint.sh"]
