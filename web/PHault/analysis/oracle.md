# Oracle evidence

The root route discloses the relevant PHP source:

```php
$sql = "SELECT username FROM users WHERE id = " . $_GET["id"];
$res = $db->query($sql);
if (!$res) {
    die("ill try to tell him, dw");
}
$row = $res->fetch_row();
echo 'ill try to tell him, dw';
```

The registered shutdown function pads requests to at least 2 seconds. Direct
`SLEEP(4)` and `BENCHMARK(...)` probes both completed in about 2.6 seconds, so
ordinary time-based SQL injection did not provide an oracle.

The payload suffix `INTO @x` changes a successful `SELECT` into a statement
whose `mysqli::query()` result is boolean `true`. The next `fetch_row()` call
then produces a visible PHP fatal error. If the injected condition matches all
rows in `users`, `SELECT ... INTO @x` fails because it returns more than one
row, so the explicit `die()` branch is taken instead.

Observed responses:

| `id` | Response size | Distinguishing suffix |
|---|---:|---|
| `0 OR 1=1 INTO @x` | 4557 bytes | `ill try to tell him, dw` |
| `0 OR 1=0 INTO @x` | 4744 bytes | `Fatal error: ... fetch_row() on bool` |

Boolean schema probes established the following application schema before
the final extraction:

```text
tables: flag,users
flag columns: flag
users usernames: admin,guest
```

The final value is read from `(SELECT flag FROM flag LIMIT 1)` by binary
searching its length and each byte with the fatal-error oracle.
