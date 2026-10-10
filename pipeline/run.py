#!/usr/bin/env python3
"""Dopamind Deck-Pipeline: Thema -> Autor -> Pruefung -> Gate -> decks.json.

Aufruf:   python pipeline/run.py            (echter Lauf, braucht ANTHROPIC_API_KEY)
          python pipeline/run.py --dry-run  (Testlauf mit Platzhalter-Antworten, kostet nichts)
Einstellungen ueber Umgebungsvariablen (alle optional):
  DECKS_PER_RUN (3)  DAILY_BUDGET_USD (3.00)  AUTHOR_MODEL  CHECK_MODEL  BLIND_MODEL
"""
import json, os, re, sys, time, random, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIPE = ROOT / "pipeline"
DECKS = ROOT / "decks.json"
TOPICS = PIPE / "topics.json"
LOG = PIPE / "log.jsonl"
SPEC = (PIPE / "SPEC.md").read_text(encoding="utf-8")

DECKS_PER_RUN = int(os.getenv("DECKS_PER_RUN", "3"))
BUDGET = float(os.getenv("DAILY_BUDGET_USD", "3.00"))
AUTHOR_MODEL = os.getenv("AUTHOR_MODEL", "claude-sonnet-5-5")
CHECK_MODEL = os.getenv("CHECK_MODEL", "claude-sonnet-5-5")
BLIND_MODEL = os.getenv("BLIND_MODEL", "claude-haiku-4-5-20251001")
TOPIC_MODEL = os.getenv("TOPIC_MODEL", "claude-haiku-4-5-20251001")
MAX_REVISIONS = 2
CATS = ["Wirtschaft", "Politik", "Geschichte", "Ernährung", "Psyche", "Sport", "Wissenschaft", "Alltag", "Gesundheit", "Biologie"]
PRICE = {  # USD pro Million Tokens (Eingabe, Ausgabe), Stand Oktober 2026
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
}
SEARCH_USD = 0.01  # pro Websuche

DRY = "--dry-run" in sys.argv
spent = 0.0


# ---------------------------------------------------------------- API
class Fake:
    """Platzhalter-Client fuer --dry-run."""
    def __init__(self):
        self.n = 0
    def call(self, model, system, user, tools=None, max_tokens=4000):
        self.n += 1
        if "Themenvorschlag" in user:
            return json.dumps([{"k": "Alltag", "t": "Testthema A"}, {"k": "Sport", "t": "Testthema B"}, {"k": "Wirtschaft", "t": "Testthema C"}])
        if "BLINDTEST" in user:
            return json.dumps({"answers": [1, 1, 1]})
        if "PRUEFUNG" in user:
            return "```json\n" + json.dumps({"facts": "pass", "problems": [], "ped": {"A": 4, "B": 4, "C": 4, "D": 4, "E": 4}, "comparisons_ok": True, "quiz_fixes": []}) + "\n```"
        deck = {"id": "dry%d" % self.n, "t": "Trockenlauf %d" % self.n, "s": "Test", "k": "Alltag",
                "cards": [["🙂", "Karte %d dieses Testdecks. Aber was kommt als Nächstes?" % i] for i in range(1, 6)],
                "quiz": [["Frage %d?" % i, "richtig", "falsch eins", "falsch zwei", i] for i in (1, 3, 5)],
                "prod": None, "sources": [{"title": "Bundesbank", "publisher": "Bundesbank", "url": "https://www.bundesbank.de/"}],
                "ledger": [{"id": "f1", "card": 1, "claim": "x", "quote": "y", "url": "https://www.bundesbank.de/"}]}
        return "```json\n" + json.dumps(deck, ensure_ascii=False) + "\n```"


def make_client():
    if DRY:
        return Fake()
    import anthropic
    cli = anthropic.Anthropic()

    class Real:
        def call(self, model, system, user, tools=None, max_tokens=4000):
            global spent
            msgs = [{"role": "user", "content": user}]
            text = ""
            for _ in range(8):  # pause_turn: Server-Tools laufen lassen
                kw = dict(model=model, max_tokens=max_tokens, messages=msgs,
                          system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}])
                if tools:
                    kw["tools"] = tools
                r = cli.messages.create(**kw)
                pin, pout = PRICE.get(model, (2.0, 10.0))
                u = r.usage
                spent += (u.input_tokens * pin + u.output_tokens * pout) / 1e6
                spent += (getattr(u, "cache_creation_input_tokens", 0) or 0) * pin * 0.25 / 1e6
                spent += (getattr(u, "cache_read_input_tokens", 0) or 0) * pin * 0.05 / 1e6
                st = getattr(u, "server_tool_use", None)
                if st:
                    spent += (getattr(st, "web_search_requests", 0) or 0) * SEARCH_USD
                text = "".join(b.text for b in r.content if b.type == "text")
                if r.stop_reason == "pause_turn":
                    msgs = [msgs[0], {"role": "assistant", "content": r.content}]
                    continue
                return text
            return text
    return Real()


SEARCH = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8},
          {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 8, "max_content_tokens": 30000}]


# ---------------------------------------------------------------- Helfer
def log(**kw):
    kw["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")


def jparse(text):
    m = re.search(r"```json\s*(.*?)```", text, re.S)
    raw = m.group(1) if m else text
    i, j = raw.find("{"), raw.rfind("}")
    k, l = raw.find("["), raw.rfind("]")
    if k != -1 and (i == -1 or k < i):
        i, j = k, l
    return json.loads(raw[i:j + 1])


def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def validate(d, existing_ids):
    err = []
    if not re.fullmatch(r"[a-z0-9_]{2,20}", str(d.get("id", ""))): err.append("id")
    if d.get("id") in existing_ids: err.append("id doppelt")
    c = d.get("cards")
    if not (isinstance(c, list) and len(c) == 5 and all(isinstance(x, list) and len(x) == 2 and isinstance(x[1], str) for x in c)): err.append("cards")
    q = d.get("quiz")
    if not (isinstance(q, list) and len(q) == 3 and all(isinstance(x, list) and len(x) == 5 and 1 <= int(x[4]) <= 5 for x in q)): err.append("quiz")
    elif len({int(x[4]) for x in q}) != 3: err.append("quiz-karten nicht verschieden")
    s = d.get("sources")
    if not (isinstance(s, list) and 1 <= len(s) <= 3 and all(str(x.get("url", "")).startswith("https://") for x in s)): err.append("sources")
    for k in ("t", "s", "k"):
        if not d.get(k): err.append(k)
    if any(re.search(r"[–—]", x[1]) for x in (c or [])): err.append("gedankenstrich")
    return err


# ---------------------------------------------------------------- Stufen
def propose_topics(cli, decks, topics, n):
    have = [d["t"] for d in decks] + [t["t"] for t in topics]
    counts = {c: sum(1 for d in decks if d.get("k") == c) for c in CATS}
    user = ("Themenvorschlag: Schlage %d neue Themen für Wissens-Decks vor. Kategorien mit den wenigsten Decks zuerst: %s.\n"
            "Bereits vorhanden (nicht wiederholen, auch nicht sehr ähnlich): %s\n"
            "Regeln: alltagsrelevant, gut belegt, sachlich; Politik/Geschichte/Wirtschaft nur Erklär-Themen mit deutschen Institutionen als Quelle. "
            "Nicht: Diäten, Nahrungsergänzung mit Dosierung, Heilversprechen, tagesaktuelle Parteienstreit. "
            "Antwort nur als JSON-Liste [{\"k\":\"Kategorie\",\"t\":\"Titel als Frage oder Aussage\"}].") % (
        n, sorted(counts, key=counts.get)[:5], "; ".join(have[-120:]))
    out = jparse(cli.call(TOPIC_MODEL, "Du planst Themen für eine Lern-App.", user, None, 1500))
    return [x for x in out if x.get("k") in CATS and x.get("t")][:n]


AUTHOR_TASK = """Erstelle ein Deck nach der Spezifikation. Thema: "%s" (Kategorie %s). Verwende die id "%s".
Gehe so vor: Suche und öffne geeignete Quellen (nach Quellenregeln, mindestens eine deutsche oder europäische Institution, wenn es sie gibt),
schreibe erst das Ledger mit wörtlichen Zitaten, dann die 5 Karten und 3 Quizfragen.
Gib NUR ein JSON-Objekt in einem ```json Block aus, im Datenformat der Spezifikation (inklusive ledger, ohne Kommentare). Quizfragen im Format [Frage, richtig, falsch1, falsch2, Kartennummer].
Wenn du keine zwei verlässlichen geöffneten Quellen findest oder die Belege zu dünn sind, gib stattdessen {"reject":"Grund"} aus."""

REVISE_TASK = """Überarbeite das Deck. Behebe NUR die folgenden Befunde, lasse alles andere unverändert (gleiche Quellen, gleiche id).
Befunde:
%s
Aktuelles Deck:
%s
Gib das vollständige überarbeitete Deck als JSON in einem ```json Block aus (inklusive ledger)."""

CHECK_TASK = """PRUEFUNG. Du bist unabhängiger Prüfer. Öffne die Quellen (URLs im Ledger und in sources) selbst und prüfe jede Aussage der 5 Karten und der Quizfragen (richtige und falsche Antworten) gegen den Inhalt.
Bewerte zusätzlich nach der Pädagogik-Rubrik A bis E (1 bis 5) und prüfe jeden Vergleich/jedes Bild auf Verständlichkeit (Spezifikation Abschnitt Vergleiche).
Prüfe Quizregeln v1.4/v1.7 (keine Studien-/Namen-/Zahlenfragen, falsche Antworten plausibel und widerlegt, ähnliche Länge, mindestens 2 von 3 Alltagsfolgen).
Gib NUR dieses JSON in einem ```json Block aus:
{"facts":"pass"|"partial"|"fail","problems":["konkrete Befunde mit Kartennummer"],"ped":{"A":n,"B":n,"C":n,"D":n,"E":n},"comparisons_ok":true|false,"quiz_fixes":["konkrete Befunde zu Quizfragen"]}
"facts" ist nur "pass", wenn JEDE Aussage durch die geöffnete Quelle belegt ist und nichts darüber hinausgeht.

Deck:
%s"""

BLIND_TASK = """BLINDTEST. Du siehst nur Quizfragen, nicht den Lerntext. Wähle zu jeder Frage die Antwort, die du mit gesundem Menschenverstand für richtig hältst.
Gib NUR JSON aus: {"answers":[a,b,c]} mit der Nummer 1, 2 oder 3 der gewählten Antwort.

%s"""


def blind_test(cli, deck):
    qs, truth = [], []
    for i, q in enumerate(deck["quiz"]):
        opts = [q[1], q[2], q[3]]
        random.shuffle(opts)
        truth.append(opts.index(q[1]) + 1)
        qs.append("Frage %d: %s\n" % (i + 1, q[0]) + "\n".join("%d) %s" % (j + 1, o) for j, o in enumerate(opts)))
    out = jparse(cli.call(BLIND_MODEL, "Du beantwortest Quizfragen.", BLIND_TASK % "\n\n".join(qs), None, 300))
    return sum(1 for a, t in zip(out["answers"], truth) if a == t)


def gate(check, guessed):
    ped = check.get("ped", {})
    vals = [ped.get(k, 0) for k in "ABCDE"]
    ok = (check.get("facts") == "pass" and all(v >= 3 for v in vals) and sum(vals) / 5 >= 4
          and check.get("comparisons_ok", True) and guessed <= 1)
    problems = list(check.get("problems", [])) + list(check.get("quiz_fixes", []))
    if guessed > 1:
        problems.append("Blindtest: %d von 3 Quizfragen ohne Lerntext erratbar, Fragen/Falschantworten ersetzen." % guessed)
    if any(v < 4 for v in vals):
        problems.append("Pädagogik-Werte unter 4: %s" % ped)
    if not check.get("comparisons_ok", True):
        problems.append("Mindestens ein Vergleich ist nicht sofort verständlich, ersetzen oder streichen.")
    return ok, problems


def build_deck(cli, topic, decks):
    ids = {d["id"] for d in decks}
    tid = topic["id"]
    text = cli.call(AUTHOR_MODEL, SPEC, AUTHOR_TASK % (topic["t"], topic["k"], tid), SEARCH, 12000)
    deck = jparse(text)
    if "reject" in deck:
        return None, "Autor lehnt ab: " + str(deck["reject"])
    deck["id"] = tid
    for rnd in range(MAX_REVISIONS + 1):
        err = validate(deck, ids)
        if err:
            problems = ["Formatfehler: " + ", ".join(err)]
            check, guessed = {}, 0
        else:
            check = jparse(cli.call(CHECK_MODEL, SPEC, CHECK_TASK % json.dumps(deck, ensure_ascii=False), SEARCH, 6000))
            guessed = blind_test(cli, deck)
            ok, problems = gate(check, guessed)
            if ok:
                deck.pop("ledger", None); deck.pop("notes", None)
                deck.update(status="approved", ts=int(time.time() * 1000),
                            review={"date": datetime.date.today().isoformat(), "facts": "pass", "rounds": rnd + 1,
                                    "method": "Autor-Agent, unabhängige KI-Faktenprüfung gegen geöffnete Quellen, Pädagogik-Prüfung, Quiz-Blindtest"})
                return deck, "ok nach %d Runde(n)" % (rnd + 1)
        if rnd == MAX_REVISIONS or spent > BUDGET:
            return None, "abgelehnt: " + " | ".join(problems)[:600]
        deck = jparse(cli.call(AUTHOR_MODEL, SPEC, REVISE_TASK % ("\n".join("- " + p for p in problems), json.dumps(deck, ensure_ascii=False)), SEARCH, 12000))
        deck["id"] = tid
    return None, "abgelehnt"


def slug(t, taken):
    base = re.sub(r"[^a-z0-9]+", "", t.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))[:10] or "deck"
    s, n = base, 2
    while s in taken:
        s = base[:8] + str(n); n += 1
    return s


def main():
    cli = make_client()
    decks = load(DECKS, [])
    topics = load(TOPICS, [])
    queue = [t for t in topics if t["status"] == "queue"]
    if len(queue) < DECKS_PER_RUN + 2:
        taken = {d["id"] for d in decks} | {t["id"] for t in topics}
        for p in propose_topics(cli, decks, topics, DECKS_PER_RUN + 4):
            i = slug(p["t"], taken); taken.add(i)
            topics.append({"id": i, "k": p["k"], "t": p["t"], "status": "queue"})
        queue = [t for t in topics if t["status"] == "queue"]
    made = 0
    for t in queue:
        if made >= DECKS_PER_RUN or spent > BUDGET:
            break
        t["status"] = "in_arbeit"
        try:
            deck, msg = build_deck(cli, t, decks)
        except Exception as e:  # ein kaputtes Thema darf den Lauf nicht beenden
            deck, msg = None, "Fehler: %s" % str(e)[:300]
        made += 1
        if deck:
            decks.append(deck); t["status"] = "live"
        else:
            t["status"] = "abgelehnt"
        t["note"] = msg
        log(topic=t["id"], result=t["status"], msg=msg, spent_usd=round(spent, 3))
        DECKS.write_text(json.dumps(decks, ensure_ascii=False, indent=1), encoding="utf-8")
        TOPICS.write_text(json.dumps(topics, ensure_ascii=False, indent=1), encoding="utf-8")
        print("%s: %s (%.2f USD bisher)" % (t["id"], t["status"], spent))
    log(run_done=True, decks_total=len(decks), spent_usd=round(spent, 3))
    print("Fertig. Kosten dieses Laufs: %.2f USD" % spent)


if __name__ == "__main__":
    main()
