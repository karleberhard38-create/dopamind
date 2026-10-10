#!/usr/bin/env python3
"""Dopamind Deck-Pipeline (Quellenliste): sources.json -> Seitentext holen -> Deck schreiben
-> Programm-Pruefung (Zitate, Zahlen, Woerter, Cliffhanger, Quiz) -> KI-Pruefung -> decks.json.

Aufruf:
  python pipeline/run.py --fetch-test   Nur Seiten abrufen und Textmenge melden (kostet nichts)
  python pipeline/run.py                Echter Lauf (braucht ANTHROPIC_API_KEY)
  python pipeline/run.py --dry-run      Testlauf mit Platzhalter-Antworten (kostet nichts)
Einstellungen (Umgebungsvariablen, alle optional):
  DECKS_PER_RUN (2)  DAILY_BUDGET_USD (1.50)  AUTHOR_MODEL  CHECK_MODEL  BLIND_MODEL
"""
import json, os, re, sys, time, random, datetime, pathlib, io

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIPE = ROOT / "pipeline"
DECKS = ROOT / "decks.json"
SOURCES = PIPE / "sources.json"
LOG = PIPE / "log.jsonl"
REPORT = PIPE / "fetch_report.json"
SPEC = (PIPE / "SPEC.md").read_text(encoding="utf-8")

DECKS_PER_RUN = int(os.getenv("DECKS_PER_RUN", "2"))
BUDGET = float(os.getenv("DAILY_BUDGET_USD", "1.50"))
AUTHOR_MODEL = os.getenv("AUTHOR_MODEL", "claude-sonnet-5-5")
CHECK_MODEL = os.getenv("CHECK_MODEL", "claude-sonnet-5-5")
BLIND_MODEL = os.getenv("BLIND_MODEL", "claude-haiku-4-5-20251001")
MAX_REVISIONS = 2
MAX_WORDS_PER_SOURCE = 4500   # Kosten im Griff halten
MIN_WORDS = 350               # duennere Seiten taugen nicht als Quelle
CATS = ["Wirtschaft", "Politik", "Geschichte", "Ernährung", "Psyche", "Sport", "Wissenschaft", "Alltag", "Gesundheit", "Biologie"]
TIER_ORDER = {"A": 0, "A-": 1, "B+": 2, "B": 3, "B-": 4}
PRICE = {  # USD pro Million Tokens (Eingabe, Ausgabe), Stand Oktober 2026
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-haiku-5-5": (0.10, 0.50),
}

DRY = "--dry-run" in sys.argv
FETCH_TEST = "--fetch-test" in sys.argv
spent = 0.0


# ---------------------------------------------------------------- Helfer
def log(**kw):
    kw["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")


def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def jparse(text):
    m = re.search(r"```json\s*(.*?)```", text, re.S)
    raw = m.group(1) if m else text
    i, j = raw.find("{"), raw.rfind("}")
    k, l = raw.find("["), raw.rfind("]")
    if k != -1 and (i == -1 or k < i):
        i, j = k, l
    if i == -1 or j == -1:
        raise ValueError("kein JSON in der Antwort")
    return json.loads(raw[i:j + 1])


def norm(s):
    s = s.lower()
    for a, b in (("­", ""), (" ", " "), ("„", '"'), ("“", '"'), ("”", '"'), ("»", '"'), ("«", '"'),
                 ("‚", "'"), ("‘", "'"), ("’", "'"), ("–", "-"), ("—", "-"), ("‑", "-"), ("…", "...")):
        s = s.replace(a, b)
    s = re.sub(r"[\"']", "", s)
    return re.sub(r"\s+", " ", s).strip()


def words(s):
    return len(re.findall(r"\S+", s))


# ---------------------------------------------------------------- Seiten holen
def fetch_text(url):
    """Holt eine Seite oder ein PDF und gibt reinen Fliesstext zurueck."""
    import requests
    h = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
         "Accept-Language": "de-DE,de;q=0.9,en;q=0.7"}
    r = requests.get(url, headers=h, timeout=40)
    r.raise_for_status()
    ctype = r.headers.get("content-type", "").lower()
    if "pdf" in ctype or url.lower().split("?")[0].endswith(".pdf"):
        from pypdf import PdfReader
        rd = PdfReader(io.BytesIO(r.content))
        text = "\n".join((p.extract_text() or "") for p in rd.pages)
    else:
        import trafilatura
        text = trafilatura.extract(r.text, include_comments=False, include_tables=False, favor_recall=True) or ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def get_sources(topic):
    """Gibt [(Nr, source, text)] zurueck oder wirft eine Ausnahme."""
    out = []
    for n, s in enumerate(topic["sources"], 1):
        t = FAKE_TEXTS[s["url"]] if DRY else fetch_text(s["url"])
        w = words(t)
        if w < MIN_WORDS:
            raise ValueError("Quelle zu duenn oder nicht abrufbar (%d Woerter): %s" % (w, s["url"]))
        t = " ".join(re.findall(r"\S+", t)[:MAX_WORDS_PER_SOURCE]) if w > MAX_WORDS_PER_SOURCE else t
        out.append((n, s, t))
    return out


# ---------------------------------------------------------------- API
class Real:
    def __init__(self):
        import anthropic
        self.cli = anthropic.Anthropic()

    def call(self, model, system, messages, max_tokens=4000, tag=""):
        global spent
        r = self.cli.messages.create(model=model, max_tokens=max_tokens, messages=messages,
                                     system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}])
        pin, pout = PRICE.get(model, (2.0, 10.0))
        u = r.usage
        cw = getattr(u, "cache_creation_input_tokens", 0) or 0
        cr = getattr(u, "cache_read_input_tokens", 0) or 0
        cost = (u.input_tokens * pin + u.output_tokens * pout + cw * pin * 1.25 + cr * pin * 0.1) / 1e6
        spent += cost
        text = "".join(b.text for b in r.content if b.type == "text")
        log(call=tag, model=model, stop=r.stop_reason, tok_in=u.input_tokens, tok_out=u.output_tokens,
            cache_w=cw, cache_r=cr, cost_usd=round(cost, 4), spent_usd=round(spent, 3))
        return text


FAKE_TEXTS = {}


class Fake:
    """Platzhalter-Client fuer --dry-run: liefert ein Deck, das alle Programm-Pruefungen besteht."""
    def call(self, model, system, messages, max_tokens=4000, tag=""):
        first = messages[0]["content"]
        last = messages[-1]["content"]
        last = last if isinstance(last, str) else last[-1]["text"]
        if tag == "blind":
            return json.dumps({"answers": [1, 1, 1]})
        if tag == "check":
            return "```json\n" + json.dumps({"facts": "pass", "problems": [], "ped": {"A": 4, "B": 4, "C": 4, "D": 4, "E": 4}, "comparisons_ok": True, "quiz_fixes": []}) + "\n```"
        t = next(iter(FAKE_TEXTS.values()))
        sents = [x.strip() for x in re.split(r"(?<=[.!?]) ", t) if len(x.split()) > 6][:5]
        urls = re.findall(r"\((https?://[^)\s]+)\)", first[0]["text"] if isinstance(first, list) else first) or list(FAKE_TEXTS)
        base = "Das ist ein Beispielsatz für den Testlauf und hat genug Wörter, damit die Prüfung der Länge besteht. Er erzählt etwas über den Alltag und über kleine Dinge, die du kennst. "
        cards = []
        for i in range(5):
            tx = base + ("Aber wie geht es weiter?" if i < 4 else "Probier es heute einmal aus.")
            cards.append(["🙂", tx])
        deck = {"id": "dry", "t": "Trockenlauf", "s": "Test", "k": "Alltag", "cards": cards,
                "quiz": [["Frage %s zum Alltag?" % w, "Antwort richtig %s hier" % w, "Antwort falsch eins %s" % w, "Antwort falsch zwei %s" % w, i] for w, i in (("eins", 1), ("drei", 3), ("fünf", 5))],
                "prod": None,
                "ledger": [{"id": "f%d" % i, "card": i, "claim": "x", "quote": sents[i - 1], "url": urls[0]} for i in range(1, 6)]}
        return "```json\n" + json.dumps(deck, ensure_ascii=False) + "\n```"


# ---------------------------------------------------------------- Prompts
AUFTRAG = """AUFTRAG (hat Vorrang vor der Spezifikation oben, wo beide abweichen)
Du schreibst ein Deck NUR aus den mitgelieferten Quellentexten Q1 und Q2. Du hast keine Suche. Was nicht in diesen Texten steht, darf nicht auf eine Karte und nicht ins Quiz, auch nicht als Allgemeinwissen, Beispiel oder Zeitangabe.
Alle Zitate im Ledger werden WORTGETREU aus den Quellentexten kopiert (höchstens 30 Wörter am Stück, unverändert, nicht umformuliert). Das Programm prüft jedes Zitat per Textsuche. Jede Zahl auf den Karten und im Quiz muss in einem Zitat stehen.

KARTEN (genau 5)
- Karte 1: Haken (überraschende Frage, Zahl oder Widerspruch), nie eine Definition. Sage dem Leser nicht, was er denkt oder tut ("Du denkst ..." ist verboten). Die Auflösung kommt erst auf Karte 2.
- Karten 1 bis 4 enden mit einem konkreten Cliffhanger in Form einer Frage (Satzende mit Fragezeichen), der die nächste Karte beantwortet. Nie "Weißt du ...?" oder "Was meinst du?". Karte 5: Lösung oder konkrete, risikoarme Handlung ohne neuen Fachbegriff, endet ohne Frage.
- Jede Karte hat 25 bis 45 Wörter, einen Gedanken, keine Wiederholung einer Aussage von einer anderen Karte. Du-Ansprache, kurze Sätze, keine Füllwörter (absolut, enorm, massiv, ganz einfach), keine Ausrufezeichen, keine Gedankenstriche (– —). Alltagssprache, kein Studienjargon.
- Jede Karte hat mindestens einen Eintrag im Ledger. Nie stärker formulieren als die Quelle.
- Zeitabhängige Zahlen (Beträge, Raten, Stände) nur mit Jahresangabe und nur, wenn die Quelle das Jahr nennt.

QUIZ (genau 3 Fragen, drei verschiedene Karten, Format [Frage, richtig, falsch1, falsch2, Kartennummer])
- Die Kartennummer ist die Karte, auf der die richtige Antwort steht. Bevorzugt Karte 1, 5 und eine aus der Mitte.
- Prüft Kernaussage oder Warum, keine Namen, Fachwörter, Studiendetails, Zahlen zum Auswendiglernen. Mindestens 2 Fragen zu Alltagsfolgen oder Handlungen. Allein verständlich.
- Die richtige Antwort ist nicht mit gesundem Menschenverstand erratbar (Aha-Anteil).
- Falsche Antworten sind ernst gemeinte Irrtümer oder verbreitete Mythen, nicht absurd, keine Extremwerte, keine Wörter wie immer, nie, alles, nichts, komplett, sofort, ausschließlich, keine Verneinungen. Alle drei Antworten ähnlich lang und konkret, die richtige nie die längste.

AUSGABE: nur ein JSON-Objekt in einem ```json Block:
{"id":"(wird vom Programm gesetzt)","t":"Titel","s":"Kurzname, höchstens 14 Zeichen","k":"Kategorie","cards":[["Emoji","Text"], ... 5x],"quiz":[["Frage","richtig","falsch1","falsch2",Kartennr], ... 3x],"ledger":[{"id":"f1","card":1,"claim":"Aussage","quote":"wortgetreues Zitat","url":"https://..."}]}
Reichen die Quellentexte nicht für ein ehrliches Deck, gib {"reject":"Grund"} aus."""

CHECK_TASK = """PRUEFUNG. Du bist unabhängiger Prüfer. Prüfe das Deck unten ausschließlich gegen die Quellentexte Q1 und Q2 oben (du hast keine Suche).
1. Jede Aussage der 5 Karten und jede richtige und falsche Quizantwort: belegt, nicht belegt oder stärker als die Quelle?
2. Pädagogik-Rubrik A bis E (1 bis 5): A Haken, B Struktur und Cliffhanger, C Verständlichkeit in Alltagssprache, D Ehrlichkeit, E Nutzen von Karte 5 und Quizqualität.
3. Vergleiche und Bilder: sofort verständlich und treu zur Quelle?
In "problems" und "quiz_fixes" stehen NUR echte Verstöße, die geändert werden müssen (mit Kartennummer und wörtlichem Textstück). Hinweise, Geschmack und "vertretbar" gehören nicht hinein. "facts" ist "pass", wenn jede Aussage durch die Quellentexte belegt ist, "partial" nur bei einer Aussage, die über die Quelle hinausgeht, "fail" bei einer Falschaussage.
Gib NUR dieses JSON in einem ```json Block aus:
{"facts":"pass"|"partial"|"fail","problems":["..."],"ped":{"A":n,"B":n,"C":n,"D":n,"E":n},"comparisons_ok":true|false,"quiz_fixes":["..."]}

Deck:
%s"""

REVISE_TASK = """Überarbeite das Deck. Behebe NUR die folgenden Befunde, ändere sonst nichts (Cliffhanger, Haken, Fragen am Kartenende bleiben). Nutze nur die Quellentexte Q1 und Q2 oben. Zitate wörtlich aus den Quellentexten kopieren. Streiche oder entschärfe Aussagen, die nicht belegt sind.
Befunde:
%s
Gib das vollständige überarbeitete Deck im selben JSON-Format in einem ```json Block aus."""

BLIND_TASK = """BLINDTEST. Du siehst nur Quizfragen, nicht den Lerntext. Wähle zu jeder Frage die Antwort, die du mit gesundem Menschenverstand für richtig hältst.
Gib NUR JSON aus: {"answers":[a,b,c]} mit der Nummer 1, 2 oder 3 der gewählten Antwort.

%s"""


def source_block(srcs):
    parts = []
    for n, s, t in srcs:
        parts.append("=== Q%d: %s, %s (%s) ===\n%s" % (n, s["publisher"], s["title"], s["url"], t))
    return "QUELLENTEXTE (einzige erlaubte Grundlage)\n\n" + "\n\n".join(parts)


# ---------------------------------------------------------------- Programm-Pruefung
BAD_WRONG = re.compile(r"\b(immer|nie|niemals|alles|nichts|komplett|sofort|ausschließlich|stets|keineswegs|garantiert)\b", re.I)
BAD_PHRASES = ["du denkst", "weißt du", "was meinst du", "ganz einfach", "absolut", "enorm", "massiv"]
NUM = re.compile(r"\d+(?:[.,]\d+)*")


def local_check(deck, topic, srcs, existing_ids):
    err = []
    c = deck.get("cards")
    q = deck.get("quiz")
    led = deck.get("ledger")
    if not (isinstance(c, list) and len(c) == 5 and all(isinstance(x, list) and len(x) == 2 and isinstance(x[1], str) for x in c)):
        return ["Format: genau 5 Karten [Emoji, Text] nötig"]
    if not (isinstance(q, list) and len(q) == 3 and all(isinstance(x, list) and len(x) == 5 for x in q)):
        return ["Format: genau 3 Quizfragen [Frage, richtig, falsch1, falsch2, Kartennummer] nötig"]
    if not isinstance(led, list) or not led:
        return ["Format: Ledger fehlt"]
    texts = {s["url"]: norm(t) for n, s, t in srcs}
    # Ledger: Zitate wortgetreu
    quotes = []
    cards_in_ledger = set()
    for e in led:
        quote = str(e.get("quote", "")).strip().strip("…").strip()
        if e.get("url") not in texts:
            err.append("Ledger %s: URL gehört nicht zu den Quellen" % e.get("id")); continue
        if words(quote) > 45:
            err.append("Ledger %s: Zitat länger als 30 Wörter, kürze es auf einen wörtlichen Ausschnitt" % e.get("id"))
        if norm(quote) not in texts[e["url"]]:
            err.append("Ledger %s: Zitat steht nicht wörtlich im Quellentext: \"%s\"" % (e.get("id"), quote[:90]))
        quotes.append(norm(quote))
        try: cards_in_ledger.add(int(e.get("card")))
        except Exception: pass
    for i in range(1, 6):
        if i not in cards_in_ledger:
            err.append("Karte %d hat keinen Ledger-Eintrag" % i)
    qtext = " ".join(quotes)
    qnums = {x.replace(",", ".").rstrip(".") for x in NUM.findall(qtext)}
    qdigits = {re.sub(r"\D", "", x) for x in NUM.findall(qtext)}
    # Karten
    for i, card in enumerate(c, 1):
        tx = card[1].strip()
        n = words(tx)
        if not 25 <= n <= 45: err.append("Karte %d hat %d Wörter, erlaubt sind 25 bis 45" % (i, n))
        if len(tx) > 280: err.append("Karte %d ist länger als 280 Zeichen" % i)
        if re.search(r"[–—]", tx): err.append("Karte %d enthält einen Gedankenstrich" % i)
        if "!" in tx: err.append("Karte %d enthält ein Ausrufezeichen" % i)
        low = tx.lower()
        for ph in BAD_PHRASES:
            if ph in low: err.append("Karte %d enthält verbotene Formulierung \"%s\"" % (i, ph))
        if i <= 4 and not tx.rstrip(' "\'“”').endswith("?"):
            err.append("Karte %d endet nicht mit einer Cliffhanger-Frage (Fragezeichen am Ende)" % i)
        if i == 5 and tx.rstrip().endswith("?"):
            err.append("Karte 5 soll mit einer Handlung enden, nicht mit einer Frage")
        for num in NUM.findall(tx):
            d = re.sub(r"\D", "", num)
            if d in ("0", "1", "2"): continue
            if d not in qdigits and num.replace(",", ".") not in qnums:
                err.append("Karte %d: Zahl \"%s\" steht in keinem Zitat des Ledgers" % (i, num))
    # Quiz
    nums = []
    for k, e in enumerate(q, 1):
        try: nums.append(int(e[4]))
        except Exception: err.append("Quiz %d: Kartennummer fehlt" % k); continue
        if not 1 <= nums[-1] <= 5: err.append("Quiz %d: Kartennummer außerhalb 1 bis 5" % k)
        ans = [str(x) for x in e[1:4]]
        for a in ans[1:]:
            if BAD_WRONG.search(a): err.append("Quiz %d: falsche Antwort enthält Extremwort: \"%s\"" % (k, a))
        lens = [len(a) for a in ans]
        if lens[0] > 1.3 * max(lens[1:]): err.append("Quiz %d: richtige Antwort ist auffällig länger als die falschen" % k)
        if max(lens) > 1.7 * min(lens): err.append("Quiz %d: Antworten sehr unterschiedlich lang, angleichen" % k)
        for x in e[:4]:
            if re.search(r"[–—]", str(x)): err.append("Quiz %d enthält einen Gedankenstrich" % k)
        for num in NUM.findall(" ".join(ans)):
            d = re.sub(r"\D", "", num)
            if d in ("0", "1", "2"): continue
            if d not in qdigits: err.append("Quiz %d: Zahl \"%s\" steht in keinem Zitat" % (k, num))
    if len(set(nums)) != 3: err.append("Quiz: die drei Kartennummern müssen verschieden sein (jetzt %s)" % nums)
    if len(str(deck.get("s", ""))) > 14 or not deck.get("s"): err.append("Kurzname \"s\" fehlt oder ist länger als 14 Zeichen")
    return err


def gate(check, guessed):
    ped = check.get("ped", {})
    vals = [ped.get(k, 0) for k in "ABCDE"]
    ok = (check.get("facts") == "pass" and all(v >= 3 for v in vals) and sum(vals) / 5 >= 4
          and check.get("comparisons_ok", True) and guessed <= 1)
    problems = list(check.get("problems", [])) + list(check.get("quiz_fixes", []))
    if guessed > 1:
        problems.append("Blindtest: %d von 3 Quizfragen ohne Lerntext erratbar, Fragen/Falschantworten ersetzen." % guessed)
    if any(v < 4 for v in vals) and not problems:
        problems.append("Pädagogik-Werte unter 4: %s. Verbessere gezielt die schwächsten Punkte." % ped)
    if not check.get("comparisons_ok", True):
        problems.append("Mindestens ein Vergleich ist nicht sofort verständlich, ersetzen oder streichen.")
    return ok, problems


def blind_test(cli, deck):
    qs, truth = [], []
    for i, qq in enumerate(deck["quiz"]):
        opts = [qq[1], qq[2], qq[3]]
        random.shuffle(opts)
        truth.append(opts.index(qq[1]) + 1)
        qs.append("Frage %d: %s\n" % (i + 1, qq[0]) + "\n".join("%d) %s" % (j + 1, o) for j, o in enumerate(opts)))
    out = jparse(cli.call(BLIND_MODEL, "Du beantwortest Quizfragen.", [{"role": "user", "content": BLIND_TASK % "\n\n".join(qs)}], 300, "blind"))
    return sum(1 for a, t in zip(out["answers"], truth) if a == t)


# ---------------------------------------------------------------- Deck bauen
def build_deck(cli, topic, existing_ids):
    srcs = get_sources(topic)
    system = SPEC + "\n\n" + AUFTRAG
    sblock = {"type": "text", "text": source_block(srcs), "cache_control": {"type": "ephemeral"}}
    task = ('Thema: "%s" (Kategorie %s). Aufhänger-Idee: %s\nHinweis: %s\nSchreibe das Deck.'
            % (topic["t"], topic["k"], topic.get("hook", ""), topic.get("note", "") or "keiner"))
    msgs = [{"role": "user", "content": [sblock, {"type": "text", "text": task}]}]
    text = cli.call(AUTHOR_MODEL, system, msgs, 5000, "autor")
    deck = jparse(text)
    if "reject" in deck:
        return None, "Autor lehnt ab: " + str(deck["reject"])[:300]
    for rnd in range(MAX_REVISIONS + 1):
        deck["k"] = topic["k"]
        deck.setdefault("t", topic["t"])
        problems = local_check(deck, topic, srcs, existing_ids)
        check = guessed = None
        if not problems:
            cmsg = [{"role": "user", "content": [sblock, {"type": "text", "text": CHECK_TASK % json.dumps(deck, ensure_ascii=False)}]}]
            check = jparse(cli.call(CHECK_MODEL, system, cmsg, 3000, "check"))
            guessed = blind_test(cli, deck)
            ok, problems = gate(check, guessed)
            if ok:
                out = {k: deck[k] for k in ("t", "s", "k", "cards", "quiz")}
                out.update(id=topic["id"], prod=None,
                           sources=[{"publisher": s["publisher"], "title": s["title"], "url": s["url"]} for n, s, t in srcs],
                           status="approved", ts=int(time.time() * 1000),
                           review={"date": datetime.date.today().isoformat(), "facts": "pass", "rounds": rnd + 1,
                                   "method": "Quellentexte vorab abgerufen, Zitate und Zahlen per Programm geprüft, unabhängige KI-Faktenprüfung gegen den Quellentext, Pädagogik-Prüfung, Quiz-Blindtest"})
                return out, "ok nach %d Runde(n)" % (rnd + 1)
        if rnd == MAX_REVISIONS or spent > BUDGET:
            return None, ("abgelehnt (%s): " % ("Programm" if check is None else "KI")) + " | ".join(problems)[:700]
        rmsg = msgs + [{"role": "assistant", "content": json.dumps(deck, ensure_ascii=False)},
                       {"role": "user", "content": REVISE_TASK % "\n".join("- " + p for p in problems[:12])}]
        deck = jparse(cli.call(AUTHOR_MODEL, system, rmsg, 5000, "revision"))
        if "reject" in deck:
            return None, "Autor lehnt ab: " + str(deck["reject"])[:300]
    return None, "abgelehnt"


# ---------------------------------------------------------------- Hauptprogramm
def fetch_test(topics):
    rep = []
    for t in topics:
        row = {"id": t["id"], "tier": t.get("tier"), "sources": []}
        for s in t["sources"]:
            try:
                w = words(fetch_text(s["url"]))
                row["sources"].append({"url": s["url"], "words": w, "ok": w >= MIN_WORDS})
            except Exception as e:
                row["sources"].append({"url": s["url"], "words": 0, "ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])})
        row["usable"] = all(x["ok"] for x in row["sources"])
        rep.append(row)
        print("%-12s %s  %s" % (t["id"], "OK " if row["usable"] else "NEIN", [x["words"] for x in row["sources"]]), flush=True)
    REPORT.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Brauchbar: %d von %d Themen" % (sum(r["usable"] for r in rep), len(rep)))


def main():
    topics = load(SOURCES, [])
    if FETCH_TEST:
        return fetch_test(topics)
    decks = load(DECKS, [])
    if DRY:
        sample = " ".join(["Dieser Beispieltext enthält Sätze für den Testlauf der Pipeline und hat bewusst genug Wörter."] * 60)
        for t in topics:
            for s in t["sources"]:
                FAKE_TEXTS[s["url"]] = sample
    cli = Fake() if DRY else Real()
    ids = {d["id"] for d in decks}
    rep = load(REPORT, [])
    unusable = {r["id"] for r in rep if not r.get("usable")}
    queue = [t for t in topics if t["status"] == "queue" and t["id"] not in ids
             and t["id"] not in unusable and len(t["sources"]) >= 2]
    queue.sort(key=lambda t: TIER_ORDER.get(t.get("tier", "B"), 5))
    made, tech_fails = 0, 0
    for t in queue:
        if made >= DECKS_PER_RUN or spent > BUDGET or tech_fails >= 2:
            break
        tech = False
        try:
            deck, msg = build_deck(cli, t, ids)
        except Exception as e:  # ein kaputtes Thema darf den Lauf nicht beenden
            deck, msg = None, "Fehler: %s: %s" % (type(e).__name__, str(e)[:300])
            tech = True
        made += 1
        if deck:
            decks.append(deck); ids.add(deck["id"]); t["status"] = "live"; tech_fails = 0
        elif tech:
            t["fails"] = t.get("fails", 0) + 1
            t["status"] = "queue" if t["fails"] < 2 else "abgelehnt"
            tech_fails += 1
        else:
            t["status"] = "abgelehnt"
        t["note_last"] = msg[:400]
        log(topic=t["id"], result=t["status"], msg=msg, spent_usd=round(spent, 3))
        print("%s: %s (%.2f USD bisher)" % (t["id"], t["status"], spent), flush=True)
        if not DRY:
            DECKS.write_text(json.dumps(decks, ensure_ascii=False, indent=1), encoding="utf-8")
            SOURCES.write_text(json.dumps(topics, ensure_ascii=False, indent=1), encoding="utf-8")
    log(run_done=True, decks_total=len(decks), spent_usd=round(spent, 3))
    print("Fertig. Kosten dieses Laufs: %.2f USD" % spent)


if __name__ == "__main__":
    main()
