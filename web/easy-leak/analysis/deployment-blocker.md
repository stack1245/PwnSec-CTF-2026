# easy-leak discarded hypothesis

## Result

This was an intermediate, incorrect conclusion. The public Caddy endpoint on
port 3000 did block the dangling-iframe approaches described below, but the
deployment also exposed the four PHP development servers to the bot on ports
9000 through 9003. Directly visiting port 9000 bypassed Caddy and its CSP,
allowing a top-level reflected XSS to leak the bot cookie. The final solution is
documented in `../writeup/ko.md`, `../writeup/en.md`, and `../solve.py`.

## Reproduced primitive

Reflecting `<iframe name="` before the token makes the child browsing-context
name contain `TOKEN_<16 hex>`. When the vulnerable page is embedded by an
attacker, the attacker is an ancestor and can navigate the child to
`about:blank`, then read the name.

## Blocking condition

The bot creates `TOKEN` without an explicit `sameSite` value. Chromium treats
an unspecified cookie as `SameSite=Lax`. Therefore, when an external attacker
page embeds `http://127.0.0.1:3000`, the cookie is omitted. The reproduced value
is the application's fallback `TOKEN_0123456789abcdef`, not the random token
stored by `/api/report`.

Loading the vulnerable page top-level does send the cookie, but an external
opener is not an ancestor of the token-bearing child frame and cannot navigate
or read that descendant. The CSP also contains `frame-src 'none'` and
`script-src 'none'`, blocking an external dangling iframe, `srcdoc` scripts,
and `javascript:` iframe payloads.

## Live evidence

- `/api/report` completed the probes successfully after the normal 20-second visit.
- The external-frame callback never fired under `frame-src 'none'`.
- The `srcdoc` and `javascript:` callback probes never fired.
- A Playwright reproduction using a known test cookie returned
  `TOKEN_0123456789abcdef` from the cross-site iframe, proving the cookie was
  omitted rather than the parsing primitive failing.
- The challenge UI supplied by the user showed zero solves.

## Corrected conclusion

The failed tests correctly described port 3000, but incorrectly treated Caddy
as the only reachable HTTP surface. The decisive step was testing the upstream
ports shown in `entrypoint.sh` from the bot's localhost network namespace.
