# PHP Sandbox Escape — local environment

This is the exact environment the remote challenge runs, so you can develop and
test your exploit locally. The remote flag is injected at runtime; locally you
get the placeholder `pwnsec{local_test_flag}`.

## Run it

```sh
docker compose up --build
```

The service is then reachable at <http://localhost:8080/>.

> Note: the build compiles PHP from source, so the first `up` takes a while.

## Interact

Arbitrary PHP evaluation is exposed via the `cmd` POST parameter:

```sh
curl -s http://localhost:8080/index.php --data-urlencode 'cmd=echo 41+1;'
```

## The sandbox

- `disable_functions` blocks every dangerous builtin (see `src/php.ini`).
- `open_basedir` is locked to `/home/ctf/scripts` and `/tmp`.
- There is no shell.
- The real flag is only readable by root via the setuid helper `/readflag`
  (source: `src/readflag.c`).

Escape the sandbox, get native code execution, and run `/readflag`.
