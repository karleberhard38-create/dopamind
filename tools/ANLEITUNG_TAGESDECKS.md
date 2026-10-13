# Anleitung: 10 neue Decks pro Tag (für die geplante Aufgabe)

Ziel: jeden Tag 10 neue, faktisch geprüfte Decks in `decks.json`. Qualität vor Menge: lieber 7 gute als 10 fragliche.

## Ablauf
1. `git pull -q --rebase`. Vorhandene Decks ansehen (`id`, `t`), keine Themen doppeln. Bisherige Kategorien: Geschichte, Gesundheit, Wissenschaft, Wirtschaft, Alltag, Ernährung, Biologie, Psyche, Sport, Politik. Mischen, wenig Vertretene (Politik, Sport, Psyche, Biologie, Wirtschaft) bevorzugen.
2. Pro Thema: mindestens 1 seriöse Quelle (Behörde, Fachgesellschaft, Uni, Fachzeitschrift, öffentlich-rechtliche Medien) mit WebSearch/WebFetch lesen. Zahlen und Aussagen gegen die Quelle abgleichen. Nur Aussagen, die die Quelle trägt. Keine Namen von Organisationen, keine Studiendetails (Teilnehmerzahlen), keine Vergleiche/Gleichnisse in den Karten.
3. Deck schreiben: 5 Karten `[emoji, text]` mit Cliffhanger-Frage, 3 Quizfragen, Quellen.
4. Faktencheck durch einen zweiten, unabhängigen Prüfer (Agent mit model haiku, bekommt nur Deck + Quelle). Abweichungen korrigieren oder Deck verwerfen.
5. Alle Decks in `/tmp/neue.json` (Liste) schreiben, dann `python3 tools/add_decks.py /tmp/neue.json` (Prüfung), bei "ALLE PRÜFUNGEN OK" mit `--write`. Fehler beheben, nicht umgehen.
6. Commit und Push (siehe unten).

## Format (wird von tools/chk.py geprüft)
- Karten: 25 bis 45 Wörter, höchstens 280 Zeichen, kein "–", kein "—", kein "!".
- Karten 1 bis 4 enden auf "?", Karte 5 ist keine Frage.
- Verbotene Phrasen: "du denkst", "weißt du", "was meinst du", "ganz einfach", "absolut", "enorm", "massiv".
- Quiz: `[frage, richtig, falsch1, falsch2, kartennummer]`, drei verschiedene Kartennummern (1 bis 5). Falsche Antworten ohne "immer, nie, niemals, komplett, ausschließlich, keineswegs, garantiert". Richtige Antwort höchstens 1,5 mal so lang wie die längste falsche; längste/kürzeste Antwort höchstens 2,0.
- `s` (Kurzthema für die Pille) höchstens 14 Zeichen, `id` nur `[a-z0-9_]`, 2 bis 20 Zeichen, eindeutig. `t` ist der lange Titel als Frage. `k` ist die Kategorie.
- Sprache: einfaches, klares Deutsch, Du-Ansprache, ein Gedanke pro Karte, jede Karte weckt Neugier auf die nächste.

## Commit
```
git add -A
git commit -m "10 neue Decks (Datum)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -m "Claude-Session: <Sitzungslink, falls bekannt>"
git pull -q --rebase && git push -q
```

## Nicht tun
- Keine bestehenden Decks ändern. `decks_owner.json` nicht anfassen.
- Keine ungeprüften Zahlen, kein Raten. Im Zweifel Deck weglassen.
- Keinen API-Schlüssel anlegen oder ausgeben.

## Bericht am Ende
Kurz: wie viele Decks erstellt, welche Themen, was verworfen wurde und warum, Gesamtzahl der Decks, Größe von decks.json.
