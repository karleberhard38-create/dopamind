# Dopamind

**App öffnen:** https://karleberhard38-create.github.io/dopamind/
(Am Handy im Browser öffnen und über "Teilen > Zum Home-Bildschirm" ablegen.)

Die App ist eine einzelne Seite (`index.html`). Die Decks stehen in `decks.json`.
Ein täglicher Job (`.github/workflows/neue-decks.yml`) erzeugt neue Decks mit der Claude-API, prüft sie
(Faktencheck, Pädagogik, Quiz-Blindtest) und trägt nur bestandene Decks in `decks.json` ein.

## Einmalige Einrichtung (ca. 20 Minuten)

1. **GitHub**: Konto anlegen, oben rechts "New repository", Name `dopamind`, "Public", dann "uploading an existing file":
   alle Dateien und Ordner aus diesem Paket hochladen (auch den versteckten Ordner `.github`; falls der Browser ihn nicht
   mitnimmt: auf der Repository-Seite "Add file > Create new file", Name `.github/workflows/neue-decks.yml`, Inhalt einfügen).
2. **API-Konto**: platform.claude.com, Konto anlegen, unter "Billing" 10 bis 20 € aufladen und unter den Limits ein
   **monatliches Ausgabenlimit** setzen. Unter "API keys" einen Schlüssel erzeugen und kopieren.
3. **Schlüssel als Geheimnis speichern**: im Repository "Settings > Secrets and variables > Actions > New repository secret",
   Name `ANTHROPIC_API_KEY`, Wert = der Schlüssel. Den Schlüssel nie in eine Datei oder in den Chat schreiben.
4. **App veröffentlichen**: "Settings > Pages", Source "Deploy from a branch", Branch `main`, Ordner `/ (root)`. Nach etwa
   einer Minute läuft die App unter `https://<dein-name>.github.io/dopamind/`.
5. **Testlauf**: Tab "Actions" > "Neue Decks erzeugen" > "Run workflow". Danach in `pipeline/log.jsonl` die Kosten ansehen.

## Einstellungen
Repository "Settings > Secrets and variables > Actions > Variables": `DECKS_PER_RUN` (Standard 3) und
`DAILY_BUDGET_USD` (Standard 3.00). Ist die Tagesgrenze erreicht, hört der Lauf auf.

## Lokal ausprobieren ohne Kosten
`python pipeline/run.py --dry-run` (arbeitet mit Platzhaltern und ändert `decks.json`; vorher sichern).

## Was die Pipeline nicht kann
Sie ersetzt keine Prüfung durch Menschen. Stichproben der neuen Decks gehören zum Betrieb dazu.

## Ersteller-Ansicht
Bestimmte Anzeigen sind nur für den Ersteller gedacht, zum Beispiel "Deck 31 von 87" oben im Feed samt Deckliste zum direkten Springen. Tester sehen sie nicht.

Einschalten: diesen Link einmal im eigenen Browser öffnen. Der Browser merkt sich das, pro Gerät und Browser einzeln.

https://karleberhard38-create.github.io/dopamind/?owner=1

Ausschalten: diesen Link einmal öffnen.

https://karleberhard38-create.github.io/dopamind/?owner=0
