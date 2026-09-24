local css = [==[
  :root {
    --bg: #0b1226;
    --bg-2: #0e1633;
    --panel: #111a3a;
    --panel-2: #152047;
    --border: rgba(148, 163, 209, 0.14);
    --border-strong: rgba(148, 163, 209, 0.24);
    --text: #e2e8ff;
    --text-dim: #94a0c4;
    --text-mute: #64708f;
    --gold: #f5c518;
    --gold-bright: #ffd84d;
    --fire: #ff7a1a;
    --green: #7dffa0;
    --red: #ff5a52;
    --mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
    --sans: 'Space Grotesk', system-ui, -apple-system, 'Segoe UI', sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { min-height: 100%; }
  body {
    background:
      radial-gradient(ellipse 80% 40% at 50% -10%, rgba(20, 36, 90, 0.55), transparent 70%),
      var(--bg);
    color: var(--text);
    font-family: var(--sans);
    -webkit-font-smoothing: antialiased;
  }
  a { color: inherit; }

  .wrap {
    width: 100%; max-width: 1200px; margin: 0 auto;
    padding: 20px 28px 40px;
    display: flex; flex-direction: column; min-height: 100vh;
  }

  /* ---- top bar ---- */
  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    gap: 16px; flex-wrap: wrap;
    padding-bottom: 16px; border-bottom: 1px solid var(--border);
    margin-bottom: 14px;
  }
  .brand { display: flex; align-items: center; gap: 12px; text-decoration: none; }
  .brand .mark { width: 36px; height: 36px; flex: none; }
  .brand-name { font-size: 16px; font-weight: 700; letter-spacing: 0.01em; color: var(--text); display: block; }
  .brand-name b { color: var(--gold); font-weight: 700; }
  .brand-sub { font-size: 11px; color: var(--text-mute); letter-spacing: 0.08em; text-transform: uppercase; font-family: var(--mono); }
  .top-actions { display: flex; align-items: center; gap: 10px; }
  .pill {
    font-family: var(--mono); font-size: 11px; letter-spacing: 0.05em;
    color: var(--text-dim); border: 1px solid var(--border);
    padding: 6px 12px; border-radius: 999px;
    display: inline-flex; align-items: center; gap: 8px; text-decoration: none;
  }
  .pill .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); }
  .pill .dot.bad { background: var(--fire); box-shadow: 0 0 6px var(--fire); }

  /* ---- tabs ---- */
  .tabs { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 22px; }
  .tab {
    font-size: 13px; font-weight: 500; color: var(--text-dim);
    padding: 7px 14px; border-radius: 6px; text-decoration: none;
    transition: background .12s, color .12s;
  }
  .tab:hover { color: var(--text); background: rgba(148, 163, 209, 0.08); }
  .tab.active { color: var(--gold); background: rgba(245, 197, 24, 0.1); }

  /* ---- page ---- */
  .page { flex: 1; }
  .page-head { font-size: 22px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 4px; }
  .page-sub { font-size: 13.5px; color: var(--text-dim); line-height: 1.6; margin-bottom: 22px; max-width: 640px; }
  .backlink {
    font-family: var(--mono); font-size: 12px; color: var(--gold);
    text-decoration: none; display: inline-flex; align-items: center; gap: 6px; margin-bottom: 16px;
  }
  .backlink:hover { color: var(--gold-bright); }

  /* ---- stat cards ---- */
  .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
  .card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px;
  }
  .card .num { font-family: var(--mono); font-size: 30px; font-weight: 700; line-height: 1.1; }
  .card .lbl { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-mute); margin-top: 6px; font-family: var(--mono); }
  .card .lbl .n { color: var(--text-dim); }
  .card.c-open .num { color: var(--green); }
  .card.c-lost .num { color: var(--fire); }
  .card.c-wontfix .num { color: var(--gold); }
  .card.c-never .num { color: var(--text-mute); }

  /* ---- panels ---- */
  .panel {
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 18px 20px; margin-bottom: 16px;
  }
  .panel-title {
    font-family: var(--mono); font-size: 11px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--text-mute); margin-bottom: 12px;
  }
  .more {
    display: inline-block; margin-top: 12px;
    font-size: 13px; color: var(--gold); text-decoration: none;
  }
  .more:hover { color: var(--gold-bright); }

  .quick { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
  .quick a {
    display: flex; flex-direction: column; gap: 4px;
    background: var(--panel-2); border: 1px solid var(--border); border-radius: 8px;
    padding: 14px 16px; text-decoration: none; transition: border-color .12s, background .12s;
  }
  .quick a:hover { border-color: var(--border-strong); background: rgba(21, 32, 71, 0.6); }
  .quick .qt { font-size: 13.5px; font-weight: 600; }
  .quick .qd { font-size: 12px; color: var(--text-dim); line-height: 1.5; }
  .quick .qd code { font-family: var(--mono); color: var(--gold); font-size: 11.5px; }

  /* ---- tables ---- */
  table.board { width: 100%; border-collapse: collapse; font-family: var(--mono); font-size: 12.5px; }
  table.board th {
    text-align: left; font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--text-mute); padding: 8px 10px;
    border-bottom: 1px solid var(--border); white-space: nowrap;
  }
  table.board td { padding: 11px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }
  table.board tbody tr:hover td { background: rgba(148, 163, 209, 0.05); }
  table.board a.tlink { color: var(--text); text-decoration: none; }
  table.board a.tlink:hover { color: var(--gold); }
  table.board a.nlink { color: var(--gold); text-decoration: none; font-weight: 600; }
  table.board a.nlink:hover { color: var(--gold-bright); }

  .badge {
    font-family: var(--mono); font-size: 10.5px; font-weight: 700; letter-spacing: 0.06em;
    padding: 3px 9px; border-radius: 999px; border: 1px solid var(--border-strong);
    color: var(--text-dim); display: inline-block; white-space: nowrap;
  }
  .badge.open { color: var(--green); border-color: rgba(125, 255, 160, 0.4); background: rgba(125, 255, 160, 0.07); }
  .badge.wontfix { color: var(--gold); border-color: rgba(245, 197, 24, 0.4); background: rgba(245, 197, 24, 0.07); }
  .badge.lost { color: var(--fire); border-color: rgba(255, 122, 26, 0.4); background: rgba(255, 122, 26, 0.07); }
  .badge.never { color: var(--text-mute); }
  .badge.prio { color: var(--red); border-color: rgba(255, 90, 82, 0.4); background: rgba(255, 90, 82, 0.07); }
  .badge.admin { color: var(--gold); border-color: rgba(245, 197, 24, 0.4); background: rgba(245, 197, 24, 0.07); }
  .badge.agent { color: var(--text-mute); }

  /* ---- ticket detail ---- */
  .ticket-title { font-size: 19px; font-weight: 700; line-height: 1.45; margin-bottom: 14px; }
  .kv { display: grid; grid-template-columns: 150px 1fr; gap: 8px 16px; font-family: var(--mono); font-size: 12.5px; }
  .kv .k { color: var(--text-mute); letter-spacing: 0.04em; }
  .kv .v { color: var(--text); }
  .prose { font-size: 14px; line-height: 1.75; color: var(--text); }
  .muted { color: var(--text-mute); }

  /* ---- search + sql console ---- */
  .searchbar { display: flex; gap: 10px; max-width: 640px; margin-bottom: 20px; }
  .searchbar input {
    flex: 1; font-family: var(--mono); font-size: 13px; color: var(--text);
    background: var(--panel); border: 1px solid var(--border); border-radius: 8px;
    padding: 11px 14px; outline: none; transition: border-color .12s;
  }
  .searchbar input:focus { border-color: var(--gold); }
  .searchbar button {
    font-family: var(--mono); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    background: var(--gold); color: #14100a;
    border: none; border-radius: 8px; padding: 0 20px; cursor: pointer; transition: background .12s;
  }
  .searchbar button:hover { background: var(--gold-bright); }

  .sqlbox textarea {
    width: 100%; min-height: 74px; resize: vertical;
    font-family: var(--mono); font-size: 13px; color: var(--green);
    background: #0a1024; border: 1px solid var(--border); border-radius: 8px;
    padding: 12px 14px; outline: none; margin-bottom: 10px; transition: border-color .12s;
  }
  .sqlbox textarea:focus { border-color: var(--gold); }
  .sqlbox .run {
    font-family: var(--mono); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    background: var(--gold); color: #14100a; border: none; border-radius: 8px; padding: 10px 18px; cursor: pointer;
  }
  .sqlbox .run:hover { background: var(--gold-bright); }

  .empty {
    font-family: var(--mono); font-size: 12.5px; color: var(--text-dim);
    text-align: center; padding: 28px 0;
  }
  pre.out {
    font-family: var(--mono); font-size: 12.5px; line-height: 1.65; color: var(--green);
    white-space: pre-wrap; word-break: break-all; margin: 0;
  }

  code { font-family: var(--mono); color: var(--gold); }

  /* ---- forms ---- */
  .form { display: flex; flex-direction: column; gap: 8px; max-width: 380px; }
  .form label {
    font-family: var(--mono); font-size: 11px; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--text-mute); margin-top: 6px;
  }
  .form input {
    font-family: var(--mono); font-size: 13px; color: var(--text);
    background: var(--panel-2); border: 1px solid var(--border); border-radius: 8px;
    padding: 10px 14px; outline: none; transition: border-color .12s;
  }
  .form input:focus { border-color: var(--gold); }
  .form .run { align-self: flex-start; margin-top: 12px; }
  .flash {
    font-family: var(--mono); font-size: 12.5px; line-height: 1.5;
    border: 1px solid var(--border-strong); border-radius: 8px;
    padding: 12px 14px; margin-bottom: 16px;
  }
  .flash.bad { color: var(--red); border-color: rgba(255, 90, 82, 0.4); background: rgba(255, 90, 82, 0.07); }
  .flash.good { color: var(--green); border-color: rgba(125, 255, 160, 0.4); background: rgba(125, 255, 160, 0.07); }

  /* ---- footer ---- */
  footer {
    margin-top: 28px; padding-top: 16px;
    border-top: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap;
  }
  .foot-note { font-size: 12px; color: var(--text-mute); font-family: var(--mono); }
  .foot-note b { color: var(--text-dim); font-weight: 700; }
  .links { display: flex; gap: 18px; }
  .links a {
    font-size: 12px; color: var(--text-dim); text-decoration: none; font-family: var(--mono);
    transition: color .12s;
  }
  .links a:hover { color: var(--gold); }

  @media (max-width: 900px) {
    .cards { grid-template-columns: repeat(2, 1fr); }
    .quick { grid-template-columns: 1fr; }
  }
  @media (max-width: 600px) {
    .wrap { padding: 16px 16px 32px; }
    .cards { grid-template-columns: 1fr; }
    .kv { grid-template-columns: 1fr; gap: 3px 0; margin-bottom: 10px; }
  }
]==]
return css
