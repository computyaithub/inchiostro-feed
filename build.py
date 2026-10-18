#!/usr/bin/env python3
"""Genera feed.xml (RSS 2.0) e index.html dalle edizioni di Inchiostro in editions/*.json.

Ogni edizione diventa un unico elemento del feed con l'intero testo in HTML,
cosi' lo Scaricatore di notizie di KOReader la trasforma in un ePub completo
senza dover scaricare gli articoli originali.
"""
import json
import glob
import os
from datetime import datetime
from email.utils import format_datetime
from html import escape

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get("INCHIOSTRO_SITE", "https://computyaithub.github.io/inchiostro-feed")
MAX_ITEMS = 14

STYLE = (
    "<style>"
    "h1{font-size:1.6em;margin:0 0 .2em}"
    "h2{font-size:1.15em;text-transform:uppercase;letter-spacing:.08em;"
    "border-bottom:2px solid #000;padding-bottom:.2em;margin:1.6em 0 .6em}"
    "h3{font-size:1.05em;margin:1em 0 .3em}"
    ".k{font-size:.75em;text-transform:uppercase;letter-spacing:.1em;color:#444;margin:0}"
    ".d{font-size:.8em;color:#444;margin:0 0 1em}"
    "p{margin:.3em 0;text-align:justify}"
    "hr{border:0;border-top:1px solid #999;margin:1em 0}"
    ".box{border:2px solid #000;padding:.6em .8em;margin-top:.8em}"
    ".src{font-size:.8em}"
    "</style>"
)


def link(url, fonte):
    if not url or not str(url).startswith(("http://", "https://")):
        return ""
    return '<p class="src"><a href="%s">Leggi su %s</a></p>' % (escape(url, True), escape(fonte or "fonte"))


def stories(items, testo_key="testo"):
    out = []
    for i, s in enumerate(items or []):
        if i:
            out.append("<hr/>")
        if s.get("fonte"):
            out.append('<p class="k">%s</p>' % escape(s["fonte"]))
        out.append("<h3>%s</h3>" % escape(s.get("titolo", "")))
        if s.get(testo_key):
            out.append("<p>%s</p>" % escape(s[testo_key]))
        out.append(link(s.get("url"), s.get("fonte")))
    return "".join(out)


def edition_html(ed):
    parts = [STYLE]
    meta = ["Edizione del mattino", ed.get("etichetta", ed.get("data", ""))]
    if ed.get("numero"):
        meta.append("N. %s" % ed["numero"])
    if ed.get("minutiLettura"):
        meta.append("%s min" % ed["minutiLettura"])
    parts.append('<p class="d">%s</p>' % escape(" · ".join(meta)))
    parts.append("<h2>Il punto</h2><p>%s</p>" % escape(ed.get("punto", "")))
    if ed.get("mondo"):
        parts.append("<h2>Mondo</h2>" + stories(ed["mondo"]))
    if ed.get("breve"):
        parts.append("<h2>In breve</h2>")
        for i, b in enumerate(ed["breve"]):
            if i:
                parts.append("<hr/>")
            parts.append("<p>%s</p>%s" % (escape(b.get("testo", "")), link(b.get("url"), b.get("fonte"))))
    if ed.get("italia"):
        parts.append("<h2>Italia</h2>" + stories(ed["italia"]))
    c = ed.get("computy")
    if c and c.get("titolo"):
        parts.append("<h2>Per Computy</h2>" + stories([c]))
        if c.get("spunto"):
            parts.append('<div class="box"><p class="k">Spunto</p><p>%s</p></div>' % escape(c["spunto"]))
    if ed.get("approfondire"):
        parts.append("<h2>Da approfondire</h2>" + stories(ed["approfondire"], "perche"))
    if ed.get("nota"):
        parts.append('<p class="d">%s</p>' % escape(ed["nota"]))
    return "".join(parts)


def pub_date(ed):
    raw = ed.get("generataAlle") or (ed.get("data", "1970-01-01") + "T07:30:00+02:00")
    try:
        return format_datetime(datetime.fromisoformat(raw))
    except ValueError:
        return format_datetime(datetime.fromisoformat(ed["data"] + "T07:30:00+02:00"))


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "editions", "*.json")), reverse=True)[:MAX_ITEMS]
    eds = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            eds.append(json.load(fh))
    items = []
    for ed in eds:
        title = "Inchiostro · %s" % ed.get("etichetta", ed.get("data", ""))
        guid = "%s/#%s" % (SITE, ed.get("data", ""))
        items.append(
            "<item><title>%s</title><link>%s</link><guid isPermaLink=\"false\">%s</guid>"
            "<pubDate>%s</pubDate><description><![CDATA[%s]]></description></item>"
            % (escape(title), escape(SITE + "/"), escape(guid), pub_date(ed),
               edition_html(ed).replace("]]>", "]]&gt;"))
        )
    last = pub_date(eds[0]) if eds else format_datetime(datetime.now().astimezone())
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        "<title>Inchiostro</title><link>%s/</link>"
        "<description>Edizione quotidiana delle notizie sull'intelligenza artificiale</description>"
        "<language>it</language><lastBuildDate>%s</lastBuildDate>%s"
        "</channel></rss>\n" % (escape(SITE), last, "".join(items))
    )
    with open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8") as fh:
        fh.write(feed)
    latest = edition_html(eds[0]) if eds else "<p>Nessuna edizione.</p>"
    page = (
        '<!doctype html><html lang="it"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Inchiostro</title></head><body style=\"max-width:36rem;margin:2rem auto;padding:0 16px;"
        'font-family:Georgia,serif;line-height:1.55\"><h1>Inchiostro</h1>%s'
        '<p class="d"><a href="feed.xml">Feed RSS</a></p></body></html>\n' % latest
    )
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    print("feed.xml: %d edizioni" % len(eds))


if __name__ == "__main__":
    main()
