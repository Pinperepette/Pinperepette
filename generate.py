#!/usr/bin/env python3
"""Genera dark_mode.svg e light_mode.svg per il profilo GitHub.

L'arte viene letta da art.json (statica, prodotta da make_art.py).
Le statistiche vengono prese live dalle API di GitHub a ogni run.

Uso:  python3 generate.py
Env:  ACCESS_TOKEN  (opzionale) PAT con scope read:user -> abilita il conteggio commit
      USER_NAME     (opzionale) default: Pinperepette
"""

import json
import os
import urllib.request
import urllib.error
from collections import Counter
from datetime import date, datetime
from xml.sax.saxutils import escape

# ---------------------------------------------------------------------------
# CONFIG — le voci qui sotto non sono deducibili dalle API: modificale a mano.
# ---------------------------------------------------------------------------
CONFIG = {
    "handle":       "pinperepette@pirate-crew",
    "host":         "Pinperepette",   # None -> azienda e sede prese dalle API
    "os":           "macOS, Arch Linux, Windows",
    "ide":          "Neovim, VS Code",
    "birth":        None,          # es. "1976-04-23" -> Uptime = eta' vera.
                                   # None -> Uptime = eta' dell'account GitHub.
    "langs_real":   "Italiano, English",
    "hobbies_sw":   "Adversarial ML, malware analysis, RE",
    "hobbies_hw":   "SDR, homelab, saldatore",
    "hobbies_real": "Panna (il cane), il mare",
    "twitter":      "@Pinperepette",
    "role":         "Security Engineer ∩ ML Enthusiast",
}

USER = os.environ.get("USER_NAME", "Pinperepette")
TOKEN = os.environ.get("ACCESS_TOKEN", "")

# larghezza in caratteri della colonna di destra
PANEL_COLS = 62

# stesso alfabeto usato da make_art.py per indicizzare la palette
CHARSET = ("0123456789abcdefghijklmnopqrstuvwxyz"
           "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

THEMES = {
    # L'arte sta sempre su un pannello scuro (art_bg), in entrambi i temi: su
    # fondo chiaro non ci sarebbe verso di rendere un teschio bianco, e
    # invertire i toni farebbe sparire la benda nera. In tema scuro il pannello
    # coincide col fondo di GitHub, quindi non si vede; in tema chiaro diventa
    # una finestra di terminale. Cosi' l'avatar e' identico nei due temi.
    "dark_mode.svg":  dict(text="#c9d1d9", key="#f0883e", value="#58a6ff",
                           dim="#484f58", accent="#3fb950",
                           art_bg="#0d1117", art_floor=75, art_ceil=255),
    "light_mode.svg": dict(text="#1f2328", key="#7d3000", value="#032f62",
                           dim="#6e7781", accent="#116329",
                           art_bg="#0d1117", art_floor=75, art_ceil=255),
}


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------
def get_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "profile-readme-generator",
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def total_commits(login, since_year):
    """Somma i commit per anno via GraphQL. Richiede ACCESS_TOKEN."""
    if not TOKEN:
        return None
    total = 0
    for year in range(since_year, date.today().year + 1):
        q = {"query": """
            query($login:String!,$from:DateTime!,$to:DateTime!){
              user(login:$login){
                contributionsCollection(from:$from,to:$to){
                  totalCommitContributions
                  restrictedContributionsCount
                }}}""",
             "variables": {"login": login,
                           "from": f"{year}-01-01T00:00:00Z",
                           "to": f"{year}-12-31T23:59:59Z"}}
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps(q).encode(),
            headers={"Authorization": f"Bearer {TOKEN}",
                     "User-Agent": "profile-readme-generator",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                c = json.load(r)["data"]["user"]["contributionsCollection"]
            total += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        except (urllib.error.HTTPError, KeyError, TypeError):
            return None
    return total


CACHE = "stats_cache.json"


def collect():
    """Statistiche fresche dalle API; se falliscono, l'ultimo risultato buono.

    Senza token il rate limit e' 60 richieste/ora, e un profilo con molti repo
    ne consuma diverse. Meglio ripubblicare dati di ieri che un SVG a meta'.
    """
    try:
        d = fetch()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        if not os.path.exists(CACHE):
            raise
        print(f"API non raggiungibili ({e}): uso {CACHE}")
        d = json.load(open(CACHE, encoding="utf-8"))
        d["created"] = date.fromisoformat(d["created"])
        d["langs"] = Counter(d["langs"])
        return d
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump({**d, "created": d["created"].isoformat(),
                   "langs": dict(d["langs"])}, f, indent=1)
    return d


def fetch():
    user = get_json(f"https://api.github.com/users/{USER}")
    langs, stars, owned, forks = Counter(), 0, 0, 0
    page = 1
    while True:
        repos = get_json(f"https://api.github.com/users/{USER}/repos"
                         f"?per_page=100&page={page}&type=owner")
        if not repos:
            break
        for r in repos:
            if r["fork"]:
                forks += 1
                continue
            owned += 1
            stars += r["stargazers_count"]
            if r["language"]:
                langs[r["language"]] += 1
        page += 1

    created = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ").date()
    return {
        "user": user, "langs": langs, "stars": stars,
        "owned": owned, "forks": forks, "created": created,
        "commits": total_commits(USER, created.year),
    }


# ---------------------------------------------------------------------------
# Formattazione
# ---------------------------------------------------------------------------
def elapsed(start, end):
    """Differenza in anni/mesi/giorni, stile `uptime`."""
    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day
    if days < 0:
        months -= 1
        prev = (end.replace(day=1) - date.resolution)
        days += prev.day
    if months < 0:
        years -= 1
        months += 12
    return (f"{years} ann{'o' if years == 1 else 'i'}, "
            f"{months} mes{'e' if months == 1 else 'i'}, "
            f"{days} giorn{'o' if days == 1 else 'i'}")


def leader(key, value, cols=PANEL_COLS):
    """`- key: ....... value` con i puntini che allineano i valori."""
    head = f"- {key}: "
    dots = max(1, cols - len(head) - len(value) - 1)
    return head, "." * dots, f" {value}"


def rule(title, cols=PANEL_COLS):
    head = f"- {title} "
    return head, "-" * max(1, cols - len(head) - 1) + "."


def panel(d):
    """Ritorna una lista di righe; ogni riga e' una lista di (classe, testo)."""
    u, L = d["user"], d["langs"]
    today = date.today()

    if CONFIG["birth"]:
        up = elapsed(datetime.strptime(CONFIG["birth"], "%Y-%m-%d").date(), today)
    else:
        up = elapsed(d["created"], today)

    top = [k for k, _ in L.most_common(6)]
    prog = [k for k in top if k not in ("HTML", "CSS", "Shell")][:5]
    comp = [k for k in ("HTML", "CSS", "Shell") if k in L] + ["YAML", "JSON", "Markdown"]

    rows = []

    def kv(k, v):
        h, dots, val = leader(k, v)
        rows.append([("cc", h[:2]), ("key", h[2:-2]), ("cc", ": "),
                     ("cc", dots), ("value", val)])

    def sep(title):
        h, dashes = rule(title)
        rows.append([("cc", h[:2]), ("key", h[2:-1]), ("cc", " " + dashes)])

    def blank():
        rows.append([])

    rows.append([("hdr", CONFIG["handle"])])
    rows.append([("cc", "-" * len(CONFIG["handle"]))])

    kv("OS", CONFIG["os"])
    kv("Uptime", up)
    kv("Host", CONFIG["host"] or
       f"{u.get('company') or '—'}, {u.get('location') or '—'}")
    kv("Kernel", CONFIG["role"])
    kv("IDE", CONFIG["ide"])
    blank()
    kv("Languages.Programming", ", ".join(prog))
    kv("Languages.Computer", ", ".join(comp[:5]))
    kv("Languages.Real", CONFIG["langs_real"])
    blank()
    kv("Hobbies.Software", CONFIG["hobbies_sw"])
    kv("Hobbies.Hardware", CONFIG["hobbies_hw"])
    kv("Hobbies.Real", CONFIG["hobbies_real"])
    blank()
    sep("Contact")
    kv("Email", u.get("email") or "pinperepette@gmail.com")
    kv("Twitter", CONFIG["twitter"])
    kv("Website", (u.get("blog") or "").replace("http://", "").replace("https://", "").rstrip("/"))
    kv("GitHub", f"@{u['login']}")
    blank()
    sep("GitHub Stats")
    kv("Repos", f"{d['owned']} propri, {d['forks']} fork")
    kv("Stars", f"{d['stars']:,}".replace(",", "."))
    kv("Followers", f"{u['followers']} / Following: {u['following']}")
    if d["commits"] is not None:
        kv("Commits", f"{d['commits']:,}".replace(",", "."))
    mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
            "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    c = d["created"]
    kv("Membro da", f"{c.day} {mesi[c.month - 1]} {c.year}")
    return rows


# ---------------------------------------------------------------------------
# SVG
# ---------------------------------------------------------------------------
ART_FS, ART_LH = 9, 10.4         # l'arte e' fitta: caratteri piccoli
PANEL_FS, PANEL_LH = 15, 20
PAD = 18


def fit_to_theme(hexcol, floor, ceil):
    """Rimappa la luminanza del colore nell'intervallo leggibile del tema.

    I colori dell'arte sono quelli veri dell'avatar, quindi identici nei due
    temi: su fondo scuro benda e baffi sprofondano nel nero, su fondo chiaro il
    bianco del teschio sparisce nel bianco. Non basta tagliare gli estremi (il
    bianco diventerebbe grigio chiaro, ancora invisibile): l'intera gamma viene
    compressa dentro [floor, ceil], mantenendo la tinta e i rapporti fra i toni.
    """
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    target = floor + lum * (ceil - floor) / 255
    if lum < 1:                       # nero puro: non ha tinta da preservare
        v = int(target)
        return "#%02x%02x%02x" % (v, v, v)
    k = target / lum
    return "#%02x%02x%02x" % tuple(min(255, int(v * k)) for v in (r, g, b))


def art_text(art, x0, y0, floor, ceil):
    """Emette l'ASCII art come testo, un tspan per ogni tratto di colore uguale.

    Il colore cambia spesso, ma non a ogni carattere: raggruppare i tratti
    contigui tiene il numero di tspan (e il peso del file) sotto controllo.
    """
    pal = [fit_to_theme(c, floor, ceil) for c in art["palette"]]
    out = [f'<text x="{x0}" y="{y0}" font-size="{ART_FS}px">']
    for r, (line, colors) in enumerate(zip(art["text"], art["color"])):
        y = y0 + r * ART_LH
        spans, run, start = [], colors[0], 0
        for i in range(1, len(colors) + 1):
            if i == len(colors) or colors[i] != run:
                spans.append(f'<tspan fill="{pal[CHARSET.index(run)]}">'
                             f'{escape(line[start:i])}</tspan>')
                if i < len(colors):
                    run, start = colors[i], i
        out.append(f'<tspan x="{x0}" y="{y:g}">{"".join(spans)}</tspan>')
    out.append("</text>")
    return out


def build_svg(art, rows, c):
    art_w = int(art["cols"] * ART_FS * 0.6)
    px = PAD + art_w + 40
    art_h = int(art["rows"] * ART_LH)
    panel_h = len(rows) * PANEL_LH
    height = PAD * 2 + max(art_h, panel_h)
    width = px + int(PANEL_COLS * PANEL_FS * 0.605) + PAD

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}px" height="{height}px" '
        f'font-family="ConsolasFallback,Consolas,Menlo,DejaVu Sans Mono,monospace">',
        "<style>",
        "@font-face{font-family:'ConsolasFallback';src:local('Consolas');"
        "font-display:swap;size-adjust:109%;}",
        f".hdr{{fill:{c['accent']};font-weight:bold;}}",
        f".key{{fill:{c['key']};}}",
        f".value{{fill:{c['value']};}}",
        f".cc{{fill:{c['dim']};}}",
        "text,tspan{white-space:pre;}",
        "</style>",
    ]

    # colonna sinistra: l'arte, verticalmente centrata rispetto al pannello
    ay = PAD + max(0, (panel_h - art_h) // 2)
    out.append(f'<rect x="{PAD - 10}" y="{ay - 10}" width="{art_w + 20}" '
               f'height="{art_h + 20}" rx="6" fill="{c["art_bg"]}"/>')
    out += art_text(art, PAD, ay + ART_FS, c["art_floor"], c["art_ceil"])

    # colonna destra: pannello neofetch
    ty0 = PAD + PANEL_FS + 2
    out.append(f'<text x="{px}" y="{ty0}" font-size="{PANEL_FS}px" fill="{c["text"]}">')
    for i, row in enumerate(rows):
        y = ty0 + i * PANEL_LH
        if not row:
            out.append(f'<tspan x="{px}" y="{y}"> </tspan>')
            continue
        spans = "".join(f'<tspan class="{cls}">{escape(t)}</tspan>' for cls, t in row)
        out.append(f'<tspan x="{px}" y="{y}">{spans}</tspan>')
    out.append("</text>")
    out.append("</svg>")
    return "\n".join(out)


def main():
    art = json.load(open("art.json", encoding="utf-8"))
    rows = panel(collect())
    for name, colors in THEMES.items():
        with open(name, "w", encoding="utf-8") as f:
            f.write(build_svg(art, rows, colors))
        print("scritto", name)


if __name__ == "__main__":
    main()
