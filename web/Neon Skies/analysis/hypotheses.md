# Hypotheses

## Confirmed observations

- The bot stores the flag in a host-only, secure, HttpOnly, SameSite=Strict `FLAG` cookie for the public application origin.
- The bot signs in first, then navigates the same page to the submitted HTTP(S) URL and waits eight seconds.
- `/admin` renders `FLAG` into the DOM only when a valid server-side `sid` session exists.
- The remote deployment changed both the published local password and its server-side hash; the published local credential receives HTTP 401 remotely.
- Nginx normalizes paths for location selection but forwards the original request target upstream. Encoded traversal variants reached the Crystal application but remained encoded in `request.path` and did not become `/admin`.
- The public host's container ports 3000, 3001, and 8000 were not externally reachable.
- The supplied endpoint later returned `404 Deployment not found`, confirming instance expiry.

## H1: Direct reflected XSS in the Crystal application

- Predicts: an attacker-controlled request path or login username becomes executable markup.
- Falsifier: the exact payload is HTML-escaped or remains percent-encoded in the response.
- Evidence: login username characters `"><script>...` became `&quot;&gt;&lt;script&gt;...`; percent-encoded path markup remained percent-encoded inside an `HTML.escape` sink.
- Verdict: refuted.

## H2: Published local credentials work remotely

- Predicts: `archivist` and the published local password produce HTTP 302 and a `sid` cookie.
- Falsifier: HTTP 401 from `/login`.
- Evidence: the remote endpoint returned HTTP 401. Local SHA-256 calculations match the published compose hashes, proving the test used the intended local pair.
- Verdict: refuted.

## H3: HTTP redirect to a `javascript:` URL executes in the authenticated admin document

- Predicts: after the page is on `/admin`, navigating to an HTTP endpoint returning `Location: javascript:...` changes the existing document.
- Falsifier: Chromium rejects the redirect and leaves the original document unchanged.
- Evidence: local Chromium returned `net::ERR_ABORTED`; the URL and title stayed on the control admin document. HTTP 204, 205, and 304 plus `Refresh: javascript:...` also left it unchanged without script execution.
- Verdict: refuted.

## H4: Same-host exposed container port enables cookie-boundary abuse

- Predicts: the public hostname accepts connections on 3000, 3001, or 8000.
- Falsifier: connection timeout on all published container ports.
- Evidence: HTTP and HTTPS probes to those three ports timed out; only the public HTTPS ingress had responded before expiry.
- Verdict: refuted for external access; internal-only reachability remains expected.

## H5: Browser-side navigation or XS-Leak primitive

- Mechanism: the submitted HTTP(S) navigation must either execute in the retained `/admin` context, poison a same-host cookie, or provide an observable oracle over the protected DOM.
- Predicts: one controlled navigation produces a repeatable, content-dependent effect.
- Current evidence: text-fragment timing measurements were dominated by browser startup variance and did not yield a repeatable match oracle. The application sets X-Frame-Options DENY and no target code sends scroll or DOM state externally.
- Verdict: inconclusive; this remains the primary branch after source-level sink analysis.

## Next verification

- A sibling `*.chal.ctf.ae` origin under attacker control can set a `Domain=chal.ctf.ae` cookie.
- The active `mouse in the house` application supplied that sibling origin through its confirmed PrismJS module-import gadget.
- Two attacker cookies named `FLAG`, at `/admin` and `/`, surround the older host-only flag in browser order. Crystal 1.18.2 overwrites duplicate cookie names while parsing, so the final root-path attacker value becomes the raw `@flag` HTML sink.
- The injected handler deletes both domain cookies, fetches `/admin` again, and reads the now-unshadowed HttpOnly flag from the response body.
- Remote end-to-end execution recovered `pwnsec{7f655c6d59355727}`.
- Verdict: solved.
