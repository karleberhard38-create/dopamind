# Dopamind Deck-Pipeline (Spezifikation v1.4)

Ziel: Aus einem Thema entsteht ein Deck (5 Karten + 3 Quizfragen + Quellen), das belegbar korrekt ist.
Grundregel: **Nur was in einer Quelle steht, darf auf einer Karte stehen.** Keine Behauptung aus dem Gedächtnis.

## Stufen
1. Thema (Titel, Kategorie, Winkel/Hook)
2. Recherche + Entwurf (Autor-Agent): Faktenliste ("ledger") mit wörtlichem Zitat aus der Quelle, dann Karten daraus
3. Faktenprüfung (unabhängiger Agent, sieht nur Karten + Ledger + URLs, öffnet die Quellen selbst): pro Aussage pass / partial / fail
4. Pädagogik-Review (zweiter unabhängiger Agent, Rubrik unten)
5. Gate: Faktenprüfung ohne fail/partial UND Pädagogik >= 4 von 5 in jeder Zeile -> `approved`. Sonst Überarbeitung (max. 2 Runden), dann `rejected`.
6. Veröffentlichen in die Datenbank (Sammlung `decks`), Status `approved`, mit Prüfprotokoll.

## Quellenregeln
- Bevorzugt: Primärliteratur und Institutionen (PubMed/PMC, Cochrane, Nature/Science/Lancet/NEJM-Abstracts, NIH/NIH ODS, WHO, DGE, RKI, BfR, Fachgesellschaften, Universitäten, EFSA).
- **Deutsche Quelle (v1.6):** Zu jedem Deck suchst du aktiv, ob eine deutsche oder europäische Institution zum Thema etwas sagt (Gesundheit/Ernährung: DGE, RKI, BfR, IQWiG, AWMF-Leitlinien, BZgA/gesund.bund.de, Stiftung Warentest, Verbraucherzentrale, EFSA; Wirtschaft: Bundesbank, Destatis, BMF, ifo, DIW, IW, Bundeskartellamt; Politik/Geschichte: bpb, Bundestag, Bundesregierung, BVerfG, Bundesarchiv, Deutsches Historisches Museum). Gibt es eine, ist sie eine der angezeigten `sources` (mindestens 1 von 1 bis 3). Gibt es keine passende, steht das im Ledger-Kopf als "Deutsche Quelle: keine gefunden". Primärstudien bleiben zur Absicherung der Aussage; die deutsche Quelle ersetzt sie nicht und darf nichts anderes behaupten.
- **Wirtschaft, Politik, Geschichte (v1.6):** Hier sind deutsche bzw. europäische Institutionen die Hauptquellen (mindestens 1 der 2 Belegquellen). Internationale Quellen nur, wenn das Thema international ist (z. B. EZB, OECD, IWF, Eurostat).
- Keine Blogs, Verkaufsseiten, Wikipedia (nur als Orientierung, nie als Beleg), keine Influencer.
- Jede Zahl, Studie, Jahreszahl und Kausalbehauptung hat ein Ledger-Eintrag mit **wörtlichem Zitat (max. 30 Wörter)** aus der Seite und URL. Nur Seiten, die du wirklich geöffnet hast.
- Mindestens 2 unabhängige Quellen pro Deck, wenn irgend möglich; Kernaussage nie nur aus einer Einzelstudie, wenn es Übersichtsarbeiten gibt.
- Die letzte Karte nennt keine Aussage, die nicht im Ledger steht. Die in der App angezeigten Quellen (`sources`) sind die 1 bis 3 stärksten (Titel, Herausgeber, URL).

## Inhaltsregeln (Gesundheit besonders streng)
- Keine Heilversprechen, keine Diagnosen, keine Dosierungsempfehlungen für Medikamente. Für Nahrungsergänzung nur offizielle Referenzwerte (z. B. DGE, EFSA) nennen, wenn im Ledger.
- Unsicherheit ehrlich: "in Mäusen", "in Beobachtungsstudien", "Zusammenhang, kein Beweis" – wenn die Quelle das so sagt. Nie stärker formulieren als die Quelle.
- Kein Angst-Marketing. Neugier ja, Panik nein. Die Lösung auf Karte 5 ist eine sinnvolle, risikoarme Handlung.
- Kein Produktbutton, wenn kein Produkt wirklich passt (`prod: null`). Produkt nur bei klarer Alltagsrelevanz (z. B. Kissen, Whey), Label neutral ("… ansehen"), URL = Amazon-Suche `https://www.amazon.de/s?k=<Suchbegriff>&tag=DEIN-PARTNER-TAG`.

## Karten (genau 5)
- Karte 1: Haken (Frage, Zahl oder Widerspruch), die Auflösung kommt erst auf Karte 2.
- Karten 1 bis 4 enden mit einem **Cliffhanger** (offene Frage oder "Aber …"), Karte 5 ist die **Lösung/Handlung**.
- Jede Karte: 25 bis 45 Wörter (max. 280 Zeichen), ein einziger Gedanke, Du-Ansprache, kurzes Alltagsbeispiel (kein Bildvergleich), keine Füllwörter, keine Gedankenstriche (– —), keine Ausrufezeichen-Ketten. Deutsch, einfache Sätze. Siehe Abschnitt Sprache (v1.3).
- Ein passendes Emoji pro Karte.

## Quiz (genau 3 Fragen, jede zu einer anderen Karte; v1.7) - Regeln v1.4 (Quizqualität)
Format je Frage: [Frage, richtige Antwort, falsch1, falsch2, Kartennummer 1 bis 5]. Wähle die 3 stärksten Kernaussagen (bevorzugt Karte 1, 5 und eine Alltagsfolge aus der Mitte); lieber 3 gute Fragen als 5 mittelmäßige. Falsche Antworten müssen von den Quellen klar widerlegt sein und sind typische Irrtümer, keine Strohmänner.
Jede Frage muss mit dem Text der angegebenen Karte beantwortbar sein (die App zeigt danach diese Karte als Erklärung).
Eine Frage ist nur gut, wenn ALLE Punkte gelten:
1. Sie prüft die Kernaussage oder das Warum der Karte, so dass man danach etwas Nützliches über die Welt weiß. Nie Namen, Fachwörter, Studienjargon oder Zahlen-Auswendiglernen ("Wie heißt…", "Wie viel Prozent…", Jahr, Autor, Institut).
2. Keine Fragen über die Studie oder die Beleglage selbst ("Wie sicher sind die Belege?", "Was war die Kernfrage der Studie?", "Wie fiel der Effekt aus?"). Auch nicht "Was fanden Forschende…" ohne konkrete Aussage, sondern die Aussage selbst fragen.
3. Die Frage ist allein verständlich (ohne die Karte offen zu haben) und in Alltagssprache. Fachbegriffe stehen weder in Frage noch Antworten, außer unverzichtbar und dann erklärt.
4. Die richtige Antwort ist nicht erratbar: Ohne die Karte gelesen zu haben, würde ein kluger Laie sie nicht allein mit gesundem Menschenverstand finden. Die Antwort hat einen Aha-Anteil.
5. Falsche Antworten sind plausibel (typische Irrtümer, Mythen, Gegenteil), nicht albern, ähnlich lang wie die richtige und enthalten keine Wörter wie immer, nie, alles, nichts nur um sie falsch zu machen. Die richtige Antwort ist nicht auffällig länger oder genauer.
6. Genau eine Antwort ist richtig, laut Quelle belegt.
7. Mindestens 2 der 3 Fragen drehen sich um Alltagsfolgen oder Handlungen ("Was passiert, wenn…", "Was machst du am besten…").

## Pädagogik-Rubrik (je 1 bis 5)
A Haken: weckt die erste Karte Neugier ohne Clickbait/Falschversprechen?
B Struktur: genau ein Gedanke pro Karte, logischer Faden, Cliffhanger tragen zur nächsten Karte?
C Verständlichkeit: Würde ein Mensch ohne Vorwissen jede Karte beim ersten Lesen verstehen? Fachbegriffe nur wenn unverzichtbar und dann sofort in Alltagssprache erklärt, Beispiel/Bild, kurze Sätze, keine Füllwörter? (Wert 3 oder weniger, sobald unnötiger Fachjargon auftaucht.)
D Ehrlichkeit: Unsicherheit korrekt wiedergegeben, nichts überzogen, kein Angst-Marketing?
E Nutzen: Karte 5 liefert eine konkrete, risikoarme Handlung; Quizfragen prüfen Verständnis und sind eindeutig?
Zusätzlich: Liste konkreter Änderungswünsche pro Karte.

## Datenformat (JSON-Datei pro Deck)
{
 "id": "kurzer_slug",         // a-z, 3 bis 8 Zeichen, eindeutig
 "t": "Titel als Frage oder Aussage",
 "s": "Kurzname",             // max. 14 Zeichen, für Chips
 "k": "Kategorie",            // Gesundheit | Ernährung | Biologie | Psyche | Sport | Alltag | Wissenschaft | Politik | Geschichte | Wirtschaft
 "cards": [["😀","Text"], ... 5x],
 "quiz": [["Frage","richtig","falsch1","falsch2"], ... 5x],
 "prod": null | {"label":"…","url":"…"},
 "sources": [{"title":"…","publisher":"…","url":"…"}],   // 1 bis 3, werden in der App unter "Quelle" gezeigt
 "ledger": [{"id":"f1","card":1,"claim":"…","quote":"wörtliches Zitat","url":"…"}],
 "notes": "offene Unsicherheiten oder Hinweise für Prüfer"
}


## Zusatzregeln für den automatischen Betrieb (v1.1)
- Live-Tor: Faktenprüfung muss komplett "pass" sein (kein partial, fail, unverifiable). Pädagogik: jede Rubrikzeile mindestens 3 und Durchschnitt mindestens 4, sonst Überarbeitung. In Überarbeitungsrunden ab Runde 2 nur substanzielle Befunde beheben (Faktenprobleme, Missverständlichkeit, Falschantworten, die auch richtig sein könnten); reine Stilwünsche sind optional. Maximal 2 Überarbeitungsrunden, danach "abgelehnt".
- Ablehnen (kein Deck): weniger als 2 verlässliche, geöffnete Quellen; Thema nur durch Einzelstudien oder Meinungen belegt; Evidenz umstritten, sodass keine ehrliche 5-Karten-Version möglich ist; Gesundheitsthemen mit Diagnose- oder Dosierungsbedarf.
- Eigene Themenwahl (nur wenn weniger als 2 Aufträge offen sind): Kategorien rotieren (Gesundheit, Ernährung, Biologie, Psyche, Sport, Alltag, Wissenschaft, Politik, Geschichte, Wirtschaft), alltagsrelevant, gut belegt, kein Duplikat zu vorhandenen Decks (Sammlung decks, Feld t) oder Aufträgen (Sammlung topics). Nicht wählen: Krebsheilung, Diäten mit Gesundheitsversprechen, Nahrungsergänzung mit Dosierung, tagesaktuelle Parteienstreitfragen oder Themen, bei denen es keine sachliche Darstellung ohne Wertung gibt.
- id: a-z0-9_, 3 bis 12 Zeichen, nicht bereits in decks vorhanden.
- Bestehende Decks werden nie verändert, nur neue angelegt.
- Veröffentlichung: Dokument in Sammlung decks (doc_id = id) mit Feldern id, t, s, k, cards, quiz, prod, sources, status:"approved", ts (Date.now()), review:{facts:"pass",rounds:n,date:"JJJJ-MM-TT",method:"Autor-Agent, unabhängige KI-Faktenprüfung gegen geöffnete Quellen, Pädagogik-Review"}. Ledger und notes nicht veröffentlichen.
- Produktbutton nur, wenn es wirklich passt, sonst prod null. URL immer https://www.amazon.de/s?k=<Suchbegriff>&tag=DEIN-PARTNER-TAG.


## Kategorien Politik und Geschichte (v1.2)
Politik: Nur sachliche Erklär-Themen, z. B. wie das Grundgesetz, der Bundestag, Wahlsysteme, die EU-Institutionen, Gewaltenteilung, Gesetzgebung oder Wahlrecht funktionieren. Strikt neutral: keine Wertung, keine Parteiempfehlung, keine Partei- oder Personenwerbung, keine Prognosen, keine Ausnahme bei Aussagen über lebende Politiker. Keine Karte darf eine politische Position als richtig darstellen. Bevorzugte Quellen: bpb (Bundeszentrale für politische Bildung), Bundestag, Bundesregierung, Bundesverfassungsgericht, EU-Institutionen, Statistisches Bundesamt, Parlamentsdienste, Universitäten. Zahlen und Rechtsstand mit Datum/Stand angeben; ändert sich der Stand häufig, Thema meiden. Produktbutton immer prod:null.
Geschichte: Jahreszahlen, Namen und Ereignisse nur aus Fachliteratur oder Institutionen (Fachhistoriker, Universitäten, Museen, Archive, bpb, Landeszentralen). Unterschied zwischen belegten Fakten und Deutung kennzeichnen (\"nach Ansicht vieler Historiker\", \"Quellenlage unsicher\"). Keine Heldenverehrung, keine Verharmlosung, kein Reißen aus dem Kontext; bei Antike und Mittelalter antike Autoren nur als Quelle mit Einordnung, nie als Tatsache. Nationalsozialismus und andere Verbrechen sachlich und respektvoll, ohne Schockeffekt. Produktbutton nur bei klarem Bezug (z. B. Buch), sonst prod:null.
Für beide Kategorien gilt für den Cliffhanger: Neugier ja, Zuspitzung auf Kosten der Genauigkeit nein. Der Pädagogik-Prüfer prüft zusätzlich Neutralität (Politik) bzw. Einordnung (Geschichte) in Rubrik D.


## Vergleiche und Bilder (v1.9)
- Anschauliche Vergleiche sind erlaubt und oft hilfreich, wenn sie die Sache wirklich klarer machen. Sie müssen die Aussage der Quelle treu lassen (nichts dazuerfinden, nichts verzerren) und gehören nicht ins Ledger als Tatsache.
- Der Pädagogik-Prüfer bewertet jeden Vergleich auf Verständlichkeit: Versteht ihn jede Person ohne Vorwissen sofort? Ist er alltagsnah, kurz und nicht schief oder umständlich (schlechtes Beispiel: "ein Strich von vier Zentimetern auf einem Meterstab" für 4 von 100 Punkten, weil das Bild mehr Aufwand macht als die Zahl)? Bringt er etwas, das der reine Satz nicht bringt? Wenn nicht, wird er gestrichen oder ersetzt.
- Keine Vergleiche, die Risiken verharmlosen oder dramatisieren, und keine Größenvergleiche, die erst gerechnet werden müssen.

## Sprache: einfach statt Fachjargon (v1.3)
Ziel: Jede Karte soll jemand ohne Vorwissen (Schulniveau, kein Studium) beim ersten Lesen verstehen. Es geht um den Inhalt, nicht um Fachwörter.
- Standard ist Alltagssprache. Schreibe, was passiert, nicht wie es in der Fachwelt heißt. Beispiel: statt \"Rayleigh-Streuung\" -> \"Das Licht wird an den Luftteilchen in alle Richtungen verstreut\"; statt \"Halbwertszeit\" -> \"nach 5 Stunden ist noch die Hälfte im Körper\"; statt \"Adenosin-Rezeptoren\" -> \"Müdigkeitsstoff\".
- Fachbegriffe nur, wenn man sie braucht, um das Thema im Alltag wiederzuerkennen oder nachzuschlagen (z. B. \"Vitamin D\", \"Insulin\"). Dann höchstens EINEN neuen Begriff pro Karte und gleich in einem Halbsatz erklären. Auf Karte 5 (Handlung) kein neuer Fachbegriff.
- Studienjargon vermeiden: nicht \"Meta-Analyse\", \"Übersichtsarbeit\", \"randomisierte kontrollierte Studie\", \"Kohorte\", \"signifikant\", \"Evidenz\", \"Rezeptor\", \"Marker\". Schreibe stattdessen \"viele Studien zusammen ausgewertet\", \"Forschende teilten Menschen zufällig in zwei Gruppen\", \"deutlich\", \"Belege\".
- Zahlen nur, wenn sie hängenbleiben und nötig sind, dann mit Vergleich aus dem Alltag. Keine Prozentpunkte, Konfidenzintervalle, Dosisangaben mit Fachbegriffen.
- Kurze Sätze (meist unter 15 Wörter), aktive Verben, konkrete Bilder statt abstrakter Nomen. Keine Substantivketten, keine Nebensatzschachteln.
- Quizfragen und Antworten in derselben einfachen Sprache.
- Genauigkeit geht vor: Vereinfachen darf nie die Aussage der Quelle verändern. Wenn eine einfache Formulierung ungenau würde, lieber eine kürzere, aber korrekte Aussage wählen.
- In `sources` (Quellen-Button) dürfen Titel und Herausgeber fachlich bleiben.
- Prüfer: Faktenprüfer achtet darauf, dass die einfachere Formulierung nicht mehr behauptet als die Quelle. Pädagogik-Prüfer markiert jeden unnötigen Fachbegriff in Rubrik C und gibt eine Alltagsformulierung als Vorschlag.


## Kategorie Wirtschaft (v1.5)
Wirtschaft: Sachliche Erklär-Themen, z. B. wie Inflation, Zinsen, Steuern, Aktien und ETFs, Haushaltsbuch, Miete vs. Kauf, Lieferketten oder Preisbildung funktionieren. Keine Anlageempfehlung, keine Kauf- oder Verkaufssignale, keine Renditeversprechen, keine Prognosen als Tatsache. Zahlen nur mit Quelle und Stand (Jahr). Strikt neutral gegenüber Parteien und Konzernen. Produktbutton nur bei klarem Bezug (z. B. Buch), sonst prod:null. Pädagogik-Prüfer prüft in Rubrik D zusätzlich Neutralität und dass keine Finanzberatung entsteht.
