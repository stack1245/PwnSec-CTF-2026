# Evidence

- Original archive SHA-256: `06855f7ad1bd33f5b03e68ed1e501fbcaad5c4198aba0ca38c82ece861df46dc`.
- Archive password supplied with the challenge attachment: `infected`.
- `app/server.js` creates the flag note with an eight-hex-character ID and owner `BOT_SESSION_ID`.
- `/notes` requires `Sec-Fetch-Mode: navigate`; `/notes/:id` does not.
- A note body is rendered by markdown-it and DOMPurify, then PrismJS reads `data-prism-*` attributes.
- The following 80-byte body survives sanitization and makes Prism dynamically import `window.name`:

```html
<p data-prism-plugins data-prism-plugin-path=data:text/javascript,import(name)#>
```

- Browser reproduction showed both module loads: `data:text/javascript,import(name)#/.js` and the module URL stored in `window.name`.
- The note CSP sandbox clears `window.opener`, but a `message` event still exposes its sender as `event.source`.
- After the external parent navigates to `http://127.0.0.1:3000/notes/`, the XSS popup reads the now-same-origin parent DOM, extracts note IDs, fetches each `/notes/:id`, and navigates to the callback with the flag.
- The remote callback from the challenge bot returned `pwnsec{c723fccfe77783ae}`.
