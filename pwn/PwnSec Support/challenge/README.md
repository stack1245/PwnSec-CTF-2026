# PwnSec Support — handout

The support portal runs on an instruction set older than its incident backlog.
Please hold while your ticket is routed through 128MB of questionable architecture.

This handout contains the Docker config, the built VM, and the prebuilt guest image.

## Run directly

```sh
./l3afvm ./ctf_sql.l3af
```

Open `http://127.0.0.1:8080/`.

## Run with Docker

```sh
docker build -t pwnsec-support:handout .
docker run --rm -p 8080:8080 pwnsec-support:handout
```

Or:

```sh
docker compose up --build
```

## Optional local NGINX proxy

```sh
docker compose --profile nginx up --build
```

Then open `http://127.0.0.1:8081/`.
