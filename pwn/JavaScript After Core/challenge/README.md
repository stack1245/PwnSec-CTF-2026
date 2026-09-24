# JavaScript After Core

The remote service runs a hardened build of WebKit's `jsc` shell. You send one
JavaScript program, it runs once, the connection closes.

```
nc <host> <port> < exploit.js
```

## What is in this archive

| File | What it is |
|---|---|
| `diff.patch` | The exact patch applied to WebKit before building: the shell hardening and the `win()` gate |
| `REVISION` | The WebKit commit the build is pinned to |
| `TAG` | The WebKit tag that revision corresponds to |
| `Dockerfile` | The image the server runs, unchanged |
| `entrypoint.sh`, `run.sh` | How the service starts and how your program is executed |
| `readflag.c` | What `win()` runs on success |
| `docker-compose.yml` | Local build/run with a fake flag |

## The goal

The patch adds one host function:

```js
win(str, callback)
```

It checks that `str` reads `hello!!!`, then calls `callback(str)` twice. The
*same* string object must read `pwned!!!` after the first call and `world!!!`
after the second. Strings are immutable in JavaScript. Convince the engine
otherwise and `win()` runs `./readflag` for you.

## The shell

The patch removes the debugging and file-I/O helpers the `jsc` shell normally
offers: `addressOf`, `describe`, `describeArray`, `read`, `readFile`, `write`,
`writeFile`, `load`, `loadString`, `run`, `runString`, `openFile`, `readline`,
`createGlobalObject`, `createNonRopeNonAtomString`, `transferArrayBuffer`,
`jscOptions`, `makeMasquerader`, `getRandomSeed`, `setRandomSeed`,
`callerSourceOrigin`, `dumpTypesForAllVariables`, and `$` / `$262` with the whole
test262 agent surface.

What is left: `print`, `quit`, `gc`, `fullGC`, `edenGC`, `gcHeapSize`.

The service runs `jsc` with no extra command-line flags.

## Build it locally

The build compiles JavaScriptCore from source. Expect **40–90 minutes** on 8
cores and a large amount of disk — the WebKit checkout alone is around 16 GB.

```bash
docker compose up --build -d
echo 'print(6*7)' | nc -N localhost 1337
nc -N localhost 1337 < exploit.js
```

On a machine with less than 16 GB of RAM, lower the build parallelism:

```bash
docker compose build --build-arg PARALLEL=2
```

The target is **x86-64**. Both stages pin `--platform=linux/amd64`, so an arm64
host will build (and run) under emulation — slowly, and with different heap
layout constants than the remote.
