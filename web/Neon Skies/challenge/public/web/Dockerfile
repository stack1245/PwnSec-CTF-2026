FROM crystallang/crystal:1.18.2-alpine AS build

WORKDIR /app

COPY shard.yml ./
COPY src ./src
COPY public ./public

# ECR templates and read_file resolve against the compile cwd, so this must
# stay in /app.
RUN crystal build src/neon_skies.cr -o /app/neon_skies --release --no-debug


FROM alpine:3.20

# The ldd set of the compiled binary. Note Boehm GC is "gc" here, not "libgc".
RUN apk add --no-cache \
      gc \
      libgcc \
      libcrypto3 \
      libssl3 \
      zlib \
      zstd-libs \
      pcre2 \
      curl \
 && addgroup -S neonskies \
 && adduser -S -G neonskies neonskies

WORKDIR /app

COPY --from=build /app/neon_skies /app/neon_skies

RUN if ldd /app/neon_skies | grep -q 'not found'; then \
      echo 'ERROR: unresolved runtime libraries for /app/neon_skies:'; \
      ldd /app/neon_skies; \
      exit 1; \
    fi; \
    echo 'runtime libraries resolved:'; \
    ldd /app/neon_skies

USER neonskies

EXPOSE 3000

CMD ["/app/neon_skies"]
