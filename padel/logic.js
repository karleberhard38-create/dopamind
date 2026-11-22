/* Padel-Coach – Analyse-Logik (ohne DOM, testbar in Node)
   Landmarks pro Person: lm = Float32Array(99) [x,y,sichtbarkeit] im Bild (0..1),
                         wl = Float32Array(99) [x,y,z] in Metern (Hüftmitte = 0, z größer = weiter weg von der Kamera). */
(function (root) {
'use strict';

const OVER = ['bandeja', 'vibora', 'smash'];
const NAMES = { bandeja: 'Bandeja', vibora: 'Víbora', smash: 'Smash', vorhand: 'Vorhand', rueckhand: 'Rückhand' };

/* ================= Standard-Coaching-Config (in der App unter „Regeln“ editierbar) ================= */
const DEFAULT_CFG = {
  version: 2,
  hinweis: 'Eigene Formulierungen hier anpassen. Platzhalter: {wert} oder {wert%} (als Prozent), {schlag}. Uhr-Texte: genau 2 kurze Sätze.',
  taktikRegeln: [
    { id: 'versetzt', name: 'Loch zwischen euch', prio: 5,
      wenn: [{ wert: 'versetztAnteil', op: '>', zahl: 0.25 }],
      lage: 'Ihr steht in {versetztAnteil%} der Ballwechsel versetzt: einer vorne, einer hinten. Genau durch dieses Loch spielen die Gegner.',
      idee: 'Probier mal: gemeinsam aufrücken, gemeinsam zurück – als wärt ihr mit einem Seil verbunden. Wer lobt, ruft „vor!“.',
      uhr: ['Ihr steht oft versetzt.', 'Gemeinsam vor, gemeinsam zurück – wie am Seil.'] },
    { id: 'netz', name: 'Zu selten am Netz', prio: 5,
      wenn: [{ wert: 'netzAnteil', op: '<', zahl: 0.3 }, { wert: 'gegnerNetzAnteil', op: '>', zahl: 0.4 }],
      lage: 'Ihr seid nur {netzAnteil%} der Zeit am Netz, die Gegner {gegnerNetzAnteil%}. Wer das Netz hat, macht die Punkte.',
      idee: 'Probier mal: einen hohen Lob über die Rückhandseite spielen und dann sofort zu zweit ans Netz laufen.',
      uhr: ['Die Gegner haben das Netz, ihr nicht.', 'Hoher Lob, dann zu zweit nach vorn.'] },
    { id: 'niemandsland', name: 'Niemandsland', prio: 4,
      wenn: [{ wert: 'mitteAnteil', op: '>', zahl: 0.22 }],
      lage: 'Ihr steht {mitteAnteil%} der Zeit in der Feldmitte. Da bekommt ihr die Bälle genau vor die Füße.',
      idee: 'Probier mal: entscheide dich – ganz vor oder ganz zurück. Nach dem Aufschlag direkt durchlaufen, beim Lob der Gegner gemeinsam zurück.',
      uhr: ['Ihr bleibt oft in der Mitte stehen.', 'Ganz vor oder ganz zurück, nicht stehen bleiben.'] },
    { id: 'mitteOffen', name: 'Mitte offen', prio: 4,
      wenn: [{ wert: 'mitteOffenAnteil', op: '>', zahl: 0.3 }],
      lage: 'Zwischen euch ist oft viel Platz ({mitteOffenAnteil%} der Zeit über 6 m). Die Mitte ist euer offenes Tor.',
      idee: 'Probier mal: beide einen Schritt zur Mitte. Absprache: Die Mitte nimmt, wer die Vorhand dort hat.',
      uhr: ['Die Mitte ist offen.', 'Beide einen Schritt zur Mitte, Vorhand nimmt sie.'] },
    { id: 'eng', name: 'Zu eng', prio: 3,
      wenn: [{ wert: 'engAnteil', op: '>', zahl: 0.3 }],
      lage: 'Ihr klebt oft zusammen ({engAnteil%} der Zeit unter 2 m Abstand). Außen wird es dann frei.',
      idee: 'Probier mal: jeder bleibt in seiner Hälfte und geht nur bei Bällen in die Mitte rüber.',
      uhr: ['Ihr steht zu eng zusammen.', 'Jeder hält seine Seite, die Mitte nimmt die Vorhand.'] },
    { id: 'angespielt', name: 'Du wirst angespielt', prio: 4,
      wenn: [{ wert: 'meinSchlagAnteil', op: '>', zahl: 0.62 }],
      lage: 'Fast alles kommt zu dir ({meinSchlagAnteil%} eurer Schläge). Die Gegner haben dich als Ziel ausgesucht.',
      idee: 'Probier mal: Tempo rausnehmen und höher in die Mitte spielen, damit dein Partner ins Spiel kommt. Ruhig bleiben, lieber ein Lob mehr.',
      uhr: ['Sie spielen fast alles auf dich.', 'Tempo raus, hoch in die Mitte, Partner ins Spiel bringen.'] },
    { id: 'hintenFehler', name: 'Zu viel Risiko von hinten', prio: 5,
      wenn: [{ wert: 'endeHintenAnteil', op: '>', zahl: 0.4 }],
      lage: '{endeHintenAnteil%} der Ballwechsel enden direkt nach eurem Schlag von hinten – wahrscheinlich viele Fehler aus der Defensive.',
      idee: 'Probier mal: von hinten keinen Punkt erzwingen. Hoher Lob cross oder langsam flach vor die Füße (Chiquita), dann aufrücken.',
      uhr: ['Hinten erzwingt ihr zu viel.', 'Hoher Lob cross statt hartem Schlag.'] },
    { id: 'gelobbt', name: 'Du wirst gelobbt', prio: 3,
      wenn: [{ wert: 'ueberkopfAnteil', op: '>', zahl: 0.45 }],
      lage: '{ueberkopfAnteil%} deiner Schläge sind über Kopf. Die Gegner lobben dich, um dich vom Netz zu holen.',
      idee: 'Probier mal: Bandeja statt Smash und danach sofort wieder vor. Ein, zwei Schritte weg vom Netz, damit dich der Lob nicht überrascht.',
      uhr: ['Sie lobben dich oft.', 'Bandeja spielen und das Netz halten.'] },
    { id: 'gegnerNetz', name: 'Gegner kleben am Netz', prio: 3,
      wenn: [{ wert: 'gegnerNetzAnteil', op: '>', zahl: 0.6 }],
      lage: 'Die Gegner stehen {gegnerNetzAnteil%} der Zeit am Netz und machen von dort Druck.',
      idee: 'Probier mal: Lob höher ansetzen, über die Rückhandschulter des linken Spielers. Oder flach und langsam in die Mitte, damit sie sich bücken müssen.',
      uhr: ['Die Gegner machen am Netz Druck.', 'Lob höher über die Rückhandseite.'] },
    { id: 'kurz', name: 'Kurze Ballwechsel', prio: 2,
      wenn: [{ wert: 'schlaegeProBallwechsel', op: '<', zahl: 3.5 }],
      lage: 'Eure Ballwechsel sind kurz (im Schnitt {schlaegeProBallwechsel} Schläge). Punkte entscheiden sich schnell.',
      idee: 'Probier mal: Die ersten drei Bälle nur sicher ins Spiel bringen, Tempo kommt später.',
      uhr: ['Die Punkte enden sehr schnell.', 'Drei Bälle sicher, dann erst Tempo.'] },
    { id: 'treffpunktHinten', name: 'Treffpunkt über Kopf zu weit hinten', prio: 3,
      wenn: [{ wert: 'treffpunktHintenAnteil', op: '>', zahl: 0.45 }],
      lage: 'Bei deinen Überkopfbällen liegt der Treffpunkt oft eher hinter dem Körper ({treffpunktHintenAnteil%}).',
      idee: 'Probier mal: früher seitlich unter den Ball, mit der freien Hand auf ihn zeigen und ihn vor der Schulter treffen.',
      uhr: ['Über Kopf triffst du oft zu spät.', 'Früher drunter, Ball vor die Schulter.'] }
  ],
  fallback: {
    lage: 'Ihr steht kompakt, im Video fällt kein großes Muster auf.',
    idee: 'Probier mal: ein neues Ziel setzen – mehr Bälle in die Mitte und Lobs gezielt über die Rückhand.',
    uhr: ['Eure Struktur passt.', 'Mehr in die Mitte, Lob über die Rückhand.']
  },
  lieblingsIdeen: [
    'Bei Unsicherheit: Ball in die Mitte – da reden die Gegner aneinander vorbei.',
    'Nach jedem Lob, der über die Gegner geht: laut „vor!“ und zusammen ans Netz.',
    'Gegen schnelle Netzspieler: flach und langsam vor die Füße statt hart.',
    'Bandeja auf die Ecke der Gegner-Rückwand, nicht ins Glas knallen.'
  ],
  treffpunktKetten: [
    { wenn: [{ wert: 'schlag', ist: 'ueberkopf' }, { wert: 'tiefe', ist: 'hinten' }, { wert: 'ellbogen', op: '<', zahl: 125 }],
      kette: 'Treffpunkt eher hinter der Schulter → Ellbogen knickt ein → Ball steigt oder verliert Druck.',
      probier: 'Zwei schnelle Seitschritte zurück, freie Hand zeigt zum Ball, dann den Ball vor der Schulter treffen.',
      uhr: 'Ball vor die Schulter holen.' },
    { wenn: [{ wert: 'schlag', ist: 'ueberkopf' }, { wert: 'tiefe', ist: 'hinten' }],
      kette: 'Treffpunkt hinter dem Körper → du lehnst dich zurück, der Arm zieht nach hinten durch → Ball wird lang und knallt ins Glas.',
      probier: 'Früher seitlich drehen und weiter zurücklaufen, damit der Ball vor dir runterkommt.',
      uhr: 'Weiter zurück, Ball vor dir treffen.' },
    { wenn: [{ wert: 'schlag', ist: 'ueberkopf' }, { wert: 'hoehe', ist: 'tief' }],
      kette: 'Treffpunkt zu tief → Ellbogen sinkt unter Schulterhöhe → Ball geht ins Netz oder bleibt kurz.',
      probier: 'Früher unter den Ball laufen und ihn auf Kopfhöhe nehmen, nicht fallen lassen.',
      uhr: 'Früher unter den Ball, auf Kopfhöhe.' },
    { wenn: [{ wert: 'schlag', ist: 'ueberkopf' }, { wert: 'hoehe', ist: 'sehrhoch' }],
      kette: 'Treffpunkt ganz oben mit gestrecktem Arm → aus der {schlag} wird ein halber Smash → wenig Kontrolle, der Ball kommt von der Wand zurück.',
      probier: 'Ball etwas fallen lassen und auf Kopfhöhe mit leicht gebeugtem Ellbogen kontrolliert schneiden.',
      uhr: 'Ball kommen lassen, kontrolliert schneiden.' },
    { wenn: [{ wert: 'seite', ist: 'aussen' }],
      kette: 'Ball weit außen → Arm muss sich strecken → Ellbogen zieht nach außen → wenig Kontrolle.',
      probier: 'Kleine Anpassungsschritte, bis der Ball über bzw. neben der Schlagschulter ist.',
      uhr: 'Kleine Schritte, Ball an die Schulter.' },
    { wenn: [{ wert: 'seite', ist: 'nah' }],
      kette: 'Ball zu nah am Körper → Ellbogen klemmt → kein Schwung, der Ball wird kurz.',
      probier: 'Einen Schritt weg vom Ball machen, damit der Arm Platz hat.',
      uhr: 'Platz lassen, Schritt weg vom Ball.' },
    { wenn: [{ wert: 'schlag', ist: 'grundschlag' }, { wert: 'tiefe', ist: 'hinten' }],
      kette: 'Treffpunkt hinter dem Körper → der Arm schiebt statt zu schwingen → Ball geht hoch raus oder kommt ohne Druck.',
      probier: 'Früher ausholen und den Ball vor dem vorderen Fuß treffen.',
      uhr: 'Früh ausholen, Ball vor dem vorderen Fuß.' },
    { wenn: [{ wert: 'schlag', ist: 'grundschlag' }, { wert: 'hoehe', ist: 'tief' }, { wert: 'knie', op: '>', zahl: 150 }],
      kette: 'Tiefer Ball, aber gestreckte Beine → der Schläger kommt von oben → Ball geht ins Netz.',
      probier: 'Über die Knie runtergehen, Schlägerkopf über Handgelenkhöhe halten.',
      uhr: 'Tief über die Knie, nicht über den Rücken.' }
  ],
  treffpunktIdeal: {
    bandeja: { tiefe: ['koerper', 'vorne'], hoehe: ['mittel', 'hoch'], seite: ['ok'] },
    vibora: { tiefe: ['koerper', 'vorne'], hoehe: ['mittel', 'hoch'], seite: ['ok', 'aussen'] },
    smash: { tiefe: ['koerper', 'vorne'], hoehe: ['hoch', 'sehrhoch'], seite: ['ok'] },
    vorhand: { tiefe: ['koerper', 'vorne'], hoehe: ['mittel', 'hoch'], seite: ['ok'] },
    rueckhand: { tiefe: ['koerper', 'vorne'], hoehe: ['mittel', 'hoch'], seite: ['ok'] }
  },
  sollwerte: {
    bandeja: { elbow: [115, 165], height: [0.45, 1.15], knee: [0, 165], side: [45, 90], free: [0.3, 1] },
    vibora: { elbow: [115, 165], height: [0.3, 1.05], knee: [0, 165], side: [45, 90], free: [0.3, 1] },
    smash: { elbow: [155, 180], height: [0.85, 3], knee: [0, 158], side: [45, 90], free: [0.3, 1] },
    vorhand: { knee: [0, 150], trunk: [0, 25], reach: [0.35, 0.9], side: [35, 90] },
    rueckhand: { knee: [0, 150], trunk: [0, 25], reach: [0.35, 0.9], side: [35, 90] }
  },
  technik: {
    elbow: { name: 'Armstreckung im Treffpunkt',
      low: 'Dein Arm ist im Treffpunkt zu stark gebeugt. Triff den Ball höher und lass den Arm nach oben arbeiten.',
      high: 'Du streckst den Arm fast komplett durch, das ist eher ein Smash. Bei der {schlag} bleibt der Ellbogen leicht gebeugt.',
      uebungen: [['Schatten-Overheads', '10 Schläge ohne Ball in Zeitlupe, im Treffpunkt einfrieren und den Armwinkel prüfen. 3 Sätze.'], ['Zuwurf-Treffpunkt', 'Partner wirft hohe Bälle, du triffst nur auf Kopfhöhe vor der Schlagschulter. 3 × 10.']] },
    height: { name: 'Treffhöhe',
      low: 'Du triffst den Ball zu tief. Geh früher unter den Ball, statt ihn fallen zu lassen.',
      high: 'Du triffst den Ball sehr hoch, fast wie beim Smash. Lass ihn etwas kommen und schlag kontrollierter.',
      uebungen: [['Seitschritt-Drill', 'Hoher Lob vom Partner: seitlich zurück, Ball über der Schlagschulter treffen. 3 × 8.'], ['Ball fangen', 'Ohne Schläger hohe Bälle mit der Schlaghand am Treffpunkt fangen. 20 Wiederholungen.']] },
    knee: { name: 'Kniebeugung',
      high: 'Deine Beine sind fast gestreckt. Beug die Knie, dann kommt die Kraft aus den Beinen und nicht nur aus dem Arm.',
      high_vorhand: 'Du bleibst zu aufrecht. Padel-Bälle kommen oft tief, also geh über die Knie runter, nicht über den Rücken.',
      high_rueckhand: 'Du bleibst zu aufrecht. Padel-Bälle kommen oft tief, also geh über die Knie runter, nicht über den Rücken.',
      uebungen: [['Tiefe Bälle', 'Partner spielt tief zu, bei jedem Schlag kommst du mit der Hand fast an den Boden. 3 × 10.'], ['Split-Step + Ausfallschritt', 'Split-Step beim Schlag des Partners, dann Ausfallschritt mit gebeugtem vorderem Knie. 3 × 30 Sek.']] },
    side: { name: 'Seitstellung / Schulterdrehung',
      low: 'Du stehst beim Ausholen zu frontal. Dreh die Schultern früh seitlich ein.',
      uebungen: [['Früh eindrehen', 'Beim Zuspiel sofort die Schultern drehen, bevor du läufst. 3 × 10.'], ['Wand-Check', 'Mit der freien Schulter zur Glaswand stellen, Schattenschlag ohne früh aufzudrehen. 15 Wiederholungen.']] },
    free: { name: 'Freie Hand zeigt zum Ball',
      low: 'Deine freie Hand bleibt unten. Zeig beim Ausholen mit ihr auf den Ball, das hilft beim Timing und beim Gleichgewicht.',
      uebungen: [['Zeige-Drill', 'Bei jedem Lob zuerst mit der freien Hand auf den Ball zeigen, Schläger hinter dem Kopf. 3 × 10.'], ['Mit der Freien fangen', 'Partner wirft hoch, du fängst mit der freien Hand in Treffpunkthöhe. 20 Wiederholungen.']] },
    trunk: { name: 'Oberkörper aufrecht',
      high: 'Du knickst mit dem Oberkörper nach vorn ab. Bleib aufrecht und hol die Tiefe aus den Knien.',
      uebungen: [['Schläger auf dem Rücken', 'Schläger längs am Rücken halten, tief in die Knie gehen, ohne dass er sich löst. 3 × 10.']] },
    reach: { name: 'Abstand zum Ball',
      low: 'Du triffst den Ball zu nah am Körper. Lass mehr Platz.',
      high: 'Du musst dich zum Ball strecken. Lauf mit kleinen Schritten näher heran.',
      uebungen: [['Hütchen-Abstand', 'Hütchen eine Schlägerlänge neben dich legen, Ball immer über dem Hütchen treffen. 3 × 10.']] }
  }
};

/* ================= Geometrie ================= */
const L = (p, i) => ({ x: p.lm[i * 3], y: p.lm[i * 3 + 1], v: p.lm[i * 3 + 2] });
const Wd = (p, i) => ({ x: p.wl[i * 3], y: p.wl[i * 3 + 1], z: p.wl[i * 3 + 2] });
const mid = (a, b) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: ((a.z || 0) + (b.z || 0)) / 2 });
const sub = (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: (a.z || 0) - (b.z || 0) });
const len = v => Math.hypot(v.x, v.y, v.z || 0);
function angle(a, b, c) {
  const u = sub(a, b), w = sub(c, b);
  const d = (u.x * w.x + u.y * w.y + u.z * w.z) / ((len(u) * len(w)) || 1);
  return Math.acos(Math.max(-1, Math.min(1, d))) * 180 / Math.PI;
}
function torsoImg(p, AR) {
  const s = mid(L(p, 11), L(p, 12)), h = mid(L(p, 23), L(p, 24));
  return Math.hypot((s.x - h.x) * AR, s.y - h.y) || 0.05;
}
const footY = p => Math.max(p.lm[27 * 3 + 1], p.lm[28 * 3 + 1]);
const hipX = p => (p.lm[23 * 3] + p.lm[24 * 3]) / 2;
function pct(arr, q, def) {
  if (arr.length < 10) return def;
  const s = arr.slice().sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.max(0, Math.round(q * (s.length - 1))))];
}
function packPose(lm, wl) {
  const a = new Float32Array(99), b = new Float32Array(99);
  for (let i = 0; i < 33; i++) {
    a[i * 3] = lm[i].x; a[i * 3 + 1] = lm[i].y; a[i * 3 + 2] = lm[i].visibility == null ? 1 : lm[i].visibility;
    if (wl) { b[i * 3] = wl[i].x; b[i * 3 + 1] = wl[i].y; b[i * 3 + 2] = wl[i].z; }
  }
  return { lm: a, wl: b };
}

/* Rollen pro Bild: nL/nR = nahes Team (links/rechts aus Spielersicht), fL/fR = fernes Team.
   Nah/fern über die Rumpfgröße; fernes Team schaut zur Kamera, daher ist dessen „links“ im Bild rechts. */
function assignRoles(poses, AR) {
  const r = {};
  if (!poses.length) return r;
  const info = poses.map((p, i) => ({ i, ts: torsoImg(p, AR), fy: footY(p), x: hipX(p) }));
  const maxTs = Math.max(...info.map(o => o.ts));
  const near = info.filter(o => o.ts > 0.6 * maxTs).sort((a, b) => b.fy - a.fy).slice(0, 2);
  const far = info.filter(o => o.ts <= 0.6 * maxTs).sort((a, b) => b.ts - a.ts).slice(0, 2);
  if (near.length === 2) { near.sort((a, b) => a.x - b.x); r.nL = near[0].i; r.nR = near[1].i; }
  else if (near.length === 1) r[near[0].x < 0.5 ? 'nL' : 'nR'] = near[0].i;
  if (far.length === 2) { far.sort((a, b) => b.x - a.x); r.fL = far[0].i; r.fR = far[1].i; }
  else if (far.length === 1) r[far[0].x > 0.5 ? 'fL' : 'fR'] = far[0].i;
  return r;
}

/* ================= „Ich“-Verfolgung ================= */
const hipPos = p => { const a = L(p, 23), b = L(p, 24); return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }; };
function nearestPose(poses, pos, AR) {
  let best = null, bd = 1e9;
  poses.forEach((p, i) => { const h = hipPos(p), d = Math.hypot((h.x - pos.x) * AR, h.y - pos.y); if (d < bd) { bd = d; best = i; } });
  return best;
}
/* Verfolgt eine Person von Bild zu Bild: nächste Hüfte, ähnliche Größe, Sprung höchstens so weit,
   wie ein Spieler in der Zeit laufen kann. step(f) setzt f.me (Index in f.poses oder null). */
function makeTracker(AR, seedPos, seedTs, seedT) {
  let pos = seedPos, ts = seedTs, lastT = seedT;
  return {
    step(f) {
      const dt = Math.abs(f.t - lastT), gate = ts * Math.min(6, 1.5 + 12 * dt);
      let best = null, bd = 1e9;
      f.poses.forEach((p, i) => {
        const t2 = torsoImg(p, AR), r = t2 / ts; if (r < 0.6 || r > 1.65) return;
        const h = hipPos(p), d = Math.hypot((h.x - pos.x) * AR, h.y - pos.y);
        if (d < gate && d < bd) { bd = d; best = i; }
      });
      f.me = best;
      if (best != null) { const p = f.poses[best]; pos = hipPos(p); ts = 0.8 * ts + 0.2 * torsoImg(p, AR); lastT = f.t; }
      return best;
    }
  };
}
/* Ganze Aufnahme: vom angetippten Bild aus vorwärts und rückwärts verfolgen. */
function trackMe(frames, AR, seedT, seedPos) {
  if (!frames.length) return 0;
  let si = 0;
  for (let i = 0; i < frames.length; i++) if (Math.abs(frames[i].t - seedT) < Math.abs(frames[si].t - seedT)) si = i;
  let k = si;
  while (k < frames.length && k < si + 30 && !frames[k].poses.length) k++;
  if (k >= frames.length || !frames[k].poses.length) return 0;
  const p0 = frames[k].poses[nearestPose(frames[k].poses, seedPos, AR)], pos0 = hipPos(p0), ts0 = torsoImg(p0, AR);
  let fw = makeTracker(AR, pos0, ts0, frames[k].t), bw = makeTracker(AR, pos0, ts0, frames[k].t), hit = 0;
  for (let i = k; i < frames.length; i++) if (fw.step(frames[i]) != null) hit++;
  for (let i = k - 1; i >= 0; i--) if (bw.step(frames[i]) != null) hit++;
  return hit / frames.length;
}
/* In welchem Team und auf welcher Seite stand „ich“ in diesen Bildern meistens? */
function meIdentity(frames) {
  const n = { n: 0, f: 0, L: 0, R: 0 }; let seen = 0;
  for (const f of frames) {
    if (f.me == null) continue;
    const role = Object.keys(f.roles).find(r => f.roles[r] === f.me);
    if (!role) continue;
    seen++; n[role[0]]++; n[role[1]]++;
  }
  return { cov: frames.length ? seen / frames.length : 0, wirNah: n.n >= n.f, side: n.L >= n.R ? 'L' : 'R' };
}

/* ================= Schläge, Ballwechsel, Blöcke ================= */
function detectEvents(frames, AR, opt) {
  opt = opt || {};
  const thr = opt.thr || 5, out = [];
  for (const role of ['nL', 'nR', 'fL', 'fR']) {
    const ser = []; let prev = null;
    for (let fi = 0; fi < frames.length; fi++) {
      const f = frames[fi], pi = f.roles[role];
      if (pi == null) { prev = null; continue; }
      const p = f.poses[pi], ts = torsoImg(p, AR), w = [L(p, 15), L(p, 16)];
      if (prev && f.t > prev.t && f.t - prev.t < 0.6) {
        const dt = f.t - prev.t;
        const sp = w.map((q, k) => Math.hypot((q.x - prev.w[k].x) * AR, q.y - prev.w[k].y) / ts / dt);
        const k = sp[0] > sp[1] ? 0 : 1, sh = L(p, k === 0 ? 11 : 12);
        ser.push({ t: f.t, v: sp[k], fi, oh: w[k].y < sh.y - 0.15 * ts, wrist: k === 0 ? 'L' : 'R' });
      }
      prev = { t: f.t, w };
    }
    const sm = ser.map((s, i) => Object.assign({}, s, { v: ((ser[i - 1] || s).v + 2 * s.v + (ser[i + 1] || s).v) / 4 }));
    let last = -99;
    for (let i = 1; i < sm.length - 1; i++) {
      const s = sm[i];
      if (s.v < thr || s.v < sm[i - 1].v || s.v < sm[i + 1].v || s.t - last < 0.7) continue;
      out.push({ t: s.t, role, fi: s.fi, oh: s.oh, v: s.v, wrist: s.wrist }); last = s.t;
    }
  }
  return out.sort((a, b) => a.t - b.t);
}
function makeRallies(ev, gap) {
  gap = gap || 5; const R = []; let cur = null;
  for (const e of ev) {
    if (!cur || e.t - cur.end > gap) { cur = { start: e.t, end: e.t, ev: [] }; R.push(cur); }
    cur.ev.push(e); cur.end = e.t;
  }
  return R.filter(r => r.ev.length >= 2);
}
/* Teilt ein langes Video in Blöcke: lange Pause (Seitenwechsel/Trinkpause) oder spätestens nach ~12 Min. */
function splitBlocks(frames, AR, opt) {
  opt = opt || {};
  const pause = opt.pause || 45, maxLen = opt.maxLen || 720;
  if (!frames.length) return [];
  const rallies = makeRallies(detectEvents(frames, AR));
  const cuts = []; let blockStart = frames[0].t, n = 0;
  for (let i = 0; i < rallies.length - 1; i++) {
    n++;
    const g = rallies[i + 1].start - rallies[i].end;
    if ((g > pause && n >= 2) || (rallies[i].end - blockStart > maxLen && g > 8)) {
      const c = (rallies[i].end + rallies[i + 1].start) / 2; cuts.push(c); blockStart = c; n = 0;
    }
  }
  const bounds = [frames[0].t].concat(cuts, [frames[frames.length - 1].t + 1]);
  const blocks = [];
  for (let b = 0; b < bounds.length - 1; b++) {
    const fr = frames.filter(f => f.t >= bounds[b] && f.t < bounds[b + 1]);
    if (fr.length) blocks.push({ t0: bounds[b], t1: Math.min(bounds[b + 1], frames[frames.length - 1].t), frames: fr });
  }
  return blocks;
}

/* ================= Treffpunkt ================= */
function sideIdx(hand) {
  return hand === 'R'
    ? { sh: 12, el: 14, wr: 16, hip: 24, kn: 26, an: 28, nsh: 11, nwr: 15, nhip: 23, nkn: 25, nan: 27 }
    : { sh: 11, el: 13, wr: 15, hip: 23, kn: 25, an: 27, nsh: 12, nwr: 16, nhip: 24, nkn: 26, nan: 28 };
}
function classifyContact(p, hand, type, AR, ball) {
  const D = sideIdx(hand), schlag = OVER.includes(type) ? 'ueberkopf' : 'grundschlag';
  const ts = torsoImg(p, AR), sh = L(p, D.sh), wr = L(p, D.wr), el = L(p, D.el);
  let hoehe, h;
  if (schlag === 'ueberkopf') {
    h = (sh.y - wr.y) / ts;
    hoehe = h < 0.3 ? 'tief' : h < 0.75 ? 'mittel' : h < 1.1 ? 'hoch' : 'sehrhoch';
  } else {
    const hip = mid(L(p, 23), L(p, 24)), kn = mid(L(p, 25), L(p, 26)), shm = mid(L(p, 11), L(p, 12));
    h = (hip.y - wr.y) / ts;
    hoehe = wr.y > kn.y ? 'tief' : wr.y > hip.y ? 'mittel' : wr.y > shm.y ? 'hoch' : 'sehrhoch';
  }
  const sign = hand === 'R' ? 1 : -1;
  const s = (wr.x - sh.x) * AR * sign / ts;
  const seite = schlag === 'ueberkopf' ? (s < -0.1 ? 'nah' : s > 0.75 ? 'aussen' : 'ok') : (s < 0.35 ? 'nah' : s > 1.6 ? 'aussen' : 'ok');
  const front = type === 'rueckhand' ? D.an : D.nan;
  const dz = Wd(p, D.wr).z - Wd(p, front).z;
  const tiefe = dz < -0.05 ? 'hinten' : dz < 0.2 ? 'koerper' : 'vorne';
  const ellbogen = angle(Wd(p, D.sh), Wd(p, D.el), Wd(p, D.wr));
  const knie = (angle(Wd(p, D.hip), Wd(p, D.kn), Wd(p, D.an)) + angle(Wd(p, D.nhip), Wd(p, D.nkn), Wd(p, D.nan))) / 2;
  const vis = Math.max(0, Math.min(1, (wr.v + el.v + sh.v) / 3));
  const conf = vis * (ball ? 1 : 0.8) * 0.88;
  return { schlag, tiefe, hoehe, seite, ellbogen, knie, vals: { dz, h, s }, conf, ball: !!ball,
    stufe: conf > 0.7 ? 'hoch' : conf > 0.5 ? 'mittel' : 'niedrig' };
}
const TEXT = {
  tiefe: { hinten: 'eher hinter dem Körper', koerper: 'auf Körperhöhe', vorne: 'vor dem Körper' },
  hoehe_ueberkopf: { tief: 'unter Kopfhöhe', mittel: 'auf Kopfhöhe', hoch: 'über dem Kopf', sehrhoch: 'ganz oben, Arm gestreckt' },
  hoehe_grundschlag: { tief: 'unter Kniehöhe', mittel: 'zwischen Knie und Hüfte', hoch: 'zwischen Hüfte und Schulter', sehrhoch: 'über der Schulter' },
  seite: { nah: 'zu nah am Körper', ok: 'seitlich passend', aussen: 'weit außen' }
};
function describeContact(c) {
  return [TEXT.tiefe[c.tiefe], TEXT['hoehe_' + c.schlag][c.hoehe], TEXT.seite[c.seite]];
}
function contactIdeal(c, type, cfg) {
  const id = (cfg.treffpunktIdeal || {})[type];
  if (!id) return true;
  return ['tiefe', 'hoehe', 'seite'].every(k => !id[k] || id[k].includes(c[k]));
}
function condOk(ctx, c) {
  const v = ctx[c.wert];
  if (c.ist != null) return v === c.ist;
  if (typeof v !== 'number' || !isFinite(v)) return false;
  if (c.op === '>') return v > c.zahl;
  if (c.op === '<') return v < c.zahl;
  if (c.op === '>=') return v >= c.zahl;
  if (c.op === '<=') return v <= c.zahl;
  return false;
}
function matchChain(c, type, cfg) {
  if (contactIdeal(c, type, cfg)) return null;
  for (const ch of (cfg.treffpunktKetten || [])) if ((ch.wenn || []).every(k => condOk(c, k))) return ch;
  return null;
}

/* Ball: neongelbe, sich bewegende, kleine Flecken. data/prev = RGBA-Arrays (w×h). */
function ballCandidates(data, prev, w, h) {
  const mask = new Uint8Array(w * h);
  for (let i = 0, p = 0; p < w * h; p++, i += 4) {
    const r = data[i], g = data[i + 1], b = data[i + 2];
    if (r > 140 && g > 165 && b < 140 && g - b > 70 && r - b > 45 && Math.abs(r - g) < 75) {
      if (!prev || Math.abs(r - prev[i]) + Math.abs(g - prev[i + 1]) + Math.abs(b - prev[i + 2]) > 45) mask[p] = 1;
    }
  }
  const out = [], st = [];
  for (let p = 0; p < w * h; p++) {
    if (!mask[p]) continue;
    let n = 0, sx = 0, sy = 0; st.push(p); mask[p] = 0;
    while (st.length) {
      const q = st.pop(), x = q % w, y = (q - x) / w; n++; sx += x; sy += y;
      if (x > 0 && mask[q - 1]) { mask[q - 1] = 0; st.push(q - 1); }
      if (x < w - 1 && mask[q + 1]) { mask[q + 1] = 0; st.push(q + 1); }
      if (y > 0 && mask[q - w]) { mask[q - w] = 0; st.push(q - w); }
      if (y < h - 1 && mask[q + w]) { mask[q + w] = 0; st.push(q + w); }
    }
    if (n >= 1 && n <= 70) out.push({ x: sx / n / w, y: sy / n / h, area: n });
  }
  return out;
}
/* Wählt pro Bild den plausibelsten Ball und beschreibt den Ballflug nach dem Kontakt. */
function ballTrack(samples, tContact, wristAt, AR, torso) {
  const pts = []; let last = null;
  for (const s of samples) {
    let best = null, bd = 1e9;
    for (const c of s.cands) {
      const ref = s.t <= tContact + 0.04 ? wristAt : (last || wristAt);
      const d = Math.hypot((c.x - ref.x) * AR, c.y - ref.y) / torso;
      if (d < 1.8 && d < bd) { bd = d; best = c; }
    }
    if (best) { pts.push({ t: s.t, x: best.x, y: best.y }); if (s.t >= tContact) last = best; }
  }
  const atContact = pts.some(p => Math.abs(p.t - tContact) < 0.08);
  const after = pts.filter(p => p.t > tContact + 0.02);
  let flug = null;
  if (after.length >= 2) {
    const a = after[0], b = after[after.length - 1], dt = (b.t - a.t) || 0.03;
    const vy = (b.y - a.y) / dt / torso, vx = (b.x - a.x) * AR / dt / torso;
    flug = -vy > 2.5 && -vy > 1.5 * Math.abs(vx) ? 'steigt steil' : vy > 0.8 ? 'fällt / kommt zurück' : 'eher flach';
  }
  return { gesehen: atContact, punkte: pts.length, flug };
}

/* ================= Taktik pro Block ================= */
function analyzeBlock(frames, o) {
  const AR = o.AR, ev = detectEvents(frames, AR), rallies = makeRallies(ev);
  const W = o.wirNah ? 'n' : 'f', G = o.wirNah ? 'f' : 'n', me = W + o.side, mate = W + (o.side === 'L' ? 'R' : 'L');
  const nearFy = [], farFy = [];
  for (const f of frames) {
    for (const r of ['nL', 'nR']) if (f.roles[r] != null) nearFy.push(footY(f.poses[f.roles[r]]));
    for (const r of ['fL', 'fR']) if (f.roles[r] != null) farFy.push(footY(f.poses[f.roles[r]]));
  }
  const yNet = o.calib ? o.calib.yNet : pct(nearFy, 0.03, 0.6);
  const yBase = o.calib ? o.calib.yBase : pct(nearFy, 0.97, 0.97);
  const fNet = o.calib ? o.calib.yNet - 0.02 : pct(farFy, 0.97, 0.55);
  const fBack = pct(farFy, 0.03, 0.3);
  const depth = (role, p) => {
    const fy = footY(p);
    return role[0] === 'n' ? (fy - yNet) / ((yBase - yNet) || 1) : (fNet - fy) / ((fNet - fBack) || 1);
  };
  const zone = d => d < 0.35 ? 'netz' : d > 0.65 ? 'hinten' : 'mitte';
  let ri = 0;
  const inRally = t => { while (ri < rallies.length && rallies[ri].end + 1 < t) ri++; return ri < rallies.length && t >= rallies[ri].start - 0.3; };
  const c = { wN: 0, wNetz: 0, wMitte: 0, wHinten: 0, pair: 0, versetzt: 0, offen: 0, eng: 0, gN: 0, gNetz: 0, me: 0, mate: 0, act: 0 };
  for (const f of frames) {
    if (!inRally(f.t)) continue;
    c.act++;
    const ours = [];
    for (const r of [W + 'L', W + 'R']) {
      if (f.roles[r] == null) continue;
      const p = f.poses[f.roles[r]], d = depth(r, p), z = zone(d);
      ours.push({ p, d });
      c.wN++; if (z === 'netz') c.wNetz++; else if (z === 'mitte') c.wMitte++; else c.wHinten++;
    }
    if (f.roles[me] != null) c.me++;
    if (f.roles[mate] != null) c.mate++;
    if (ours.length === 2) {
      c.pair++;
      if (Math.abs(ours[0].d - ours[1].d) > 0.4) c.versetzt++;
      const t1 = torsoImg(ours[0].p, AR), t2 = torsoImg(ours[1].p, AR);
      const gap = Math.abs(hipX(ours[0].p) - hipX(ours[1].p)) * AR / ((t1 + t2) / 2) * 0.5;
      if (gap > 6) c.offen++; else if (gap < 2) c.eng++;
    }
    for (const r of [G + 'L', G + 'R']) {
      if (f.roles[r] == null) continue;
      c.gN++; if (zone(depth(r, f.poses[f.roles[r]])) === 'netz') c.gNetz++;
    }
  }
  const ourEv = ev.filter(e => e.role[0] === W), myEv = ev.filter(e => e.role === me);
  let endHinten = 0;
  for (const r of rallies) {
    const e = r.ev[r.ev.length - 1];
    if (e.role[0] !== W) continue;
    const f = frames[e.fi], p = f.poses[f.roles[e.role]];
    if (p && zone(depth(e.role, p)) === 'hinten') endHinten++;
  }
  const contacts = [];
  if (W === 'n') for (const e of myEv) {
    if (!e.oh) continue;
    const f = frames[e.fi], p = f.poses[f.roles[me]];
    if (p) contacts.push(classifyContact(p, o.hand, 'bandeja', AR, false));
  }
  const ratio = (a, b, min) => b >= (min || 20) ? a / b : null;
  const m = {
    spielzeitMin: frames.length ? (frames[frames.length - 1].t - frames[0].t) / 60 : 0,
    ballwechsel: rallies.length,
    schlaegeProBallwechsel: rallies.length >= 3 ? Math.round(rallies.reduce((s, r) => s + r.ev.length, 0) / rallies.length * 10) / 10 : null,
    netzAnteil: ratio(c.wNetz, c.wN), mitteAnteil: ratio(c.wMitte, c.wN), hintenAnteil: ratio(c.wHinten, c.wN),
    versetztAnteil: ratio(c.versetzt, c.pair), mitteOffenAnteil: ratio(c.offen, c.pair), engAnteil: ratio(c.eng, c.pair),
    gegnerNetzAnteil: ratio(c.gNetz, c.gN),
    meinSchlagAnteil: (c.mate > 0.5 * c.act && ourEv.length >= 6) ? myEv.length / ourEv.length : null,
    ueberkopfAnteil: myEv.length >= 5 ? myEv.filter(e => e.oh).length / myEv.length : null,
    endeHintenAnteil: rallies.length >= 4 ? endHinten / rallies.length : null,
    treffpunktHintenAnteil: contacts.length >= 3 ? contacts.filter(k => k.tiefe === 'hinten').length / contacts.length : null,
    treffpunktTiefAnteil: contacts.length >= 3 ? contacts.filter(k => k.hoehe === 'tief').length / contacts.length : null,
    ichImBild: c.act ? c.me / c.act : 0
  };
  return { m, ev, rallies, contacts, kalibriert: !!o.calib };
}

/* ================= Regeln, Texte, Uhr ================= */
function fill(text, m, type) {
  return String(text || '').replace(/\{(\w+)(%?)\}/g, (all, k, p) => {
    if (k === 'schlag') return NAMES[type] || 'Schlag';
    const v = m && m[k];
    if (typeof v !== 'number') return '–';
    return p ? Math.round(v * 100) + ' %' : String(Math.round(v * 10) / 10).replace('.', ',');
  });
}
function evalRules(m, rules) {
  const hits = [];
  for (const r of rules || []) {
    if (!r.wenn || !r.wenn.length) continue;
    let ok = true, sev = 0;
    for (const c of r.wenn) {
      if (!condOk(m, c)) { ok = false; break; }
      if (typeof c.zahl === 'number') sev += Math.abs(m[c.wert] - c.zahl) / (Math.abs(c.zahl) || 1);
    }
    if (ok) hits.push({ r, score: (r.prio || 1) * (1 + Math.min(sev, 2)) });
  }
  return hits.sort((a, b) => b.score - a.score);
}
function sentence(s) { s = String(s || '').trim(); return s && !/[.!?]$/.test(s) ? s + '.' : s; }
function watchMsg(title, rule, m, impulse, type) {
  const u = (rule && rule.uhr) || ['', ''];
  const s1 = sentence(fill(u[0], m, type));
  let s2 = sentence(fill(u[1], m, type));
  if (impulse && s2.length + impulse.length < 110) s2 = s2.replace(/[.!?]$/, '') + ', dazu: ' + sentence(impulse);
  return { titel: title, s1, s2, text: s1 + ' ' + s2 };
}
function validateCfg(c) {
  const errs = [];
  if (!c || typeof c !== 'object') return ['Keine gültige Config.'];
  if (!Array.isArray(c.taktikRegeln)) errs.push('„taktikRegeln“ muss eine Liste sein.');
  else c.taktikRegeln.forEach((r, i) => {
    if (!Array.isArray(r.wenn)) errs.push('Regel ' + (i + 1) + ': „wenn“ fehlt.');
    if (!Array.isArray(r.uhr) || r.uhr.length !== 2) errs.push('Regel ' + (i + 1) + ' (' + (r.name || r.id) + '): „uhr“ braucht genau 2 Sätze.');
  });
  if (!Array.isArray(c.treffpunktKetten)) errs.push('„treffpunktKetten“ muss eine Liste sein.');
  if (!c.sollwerte || !c.technik) errs.push('„sollwerte“ und „technik“ müssen vorhanden sein.');
  return errs;
}
function mergeCfg(user) {
  const out = JSON.parse(JSON.stringify(DEFAULT_CFG));
  if (user && typeof user === 'object') for (const k in user) out[k] = user[k];
  return out;
}

const API = { OVER, NAMES, DEFAULT_CFG, TEXT, L, Wd, mid, sub, len, angle, torsoImg, footY, hipX, pct, packPose,
  hipPos, nearestPose, makeTracker, trackMe, meIdentity, assignRoles, detectEvents, makeRallies, splitBlocks, sideIdx, classifyContact, describeContact, contactIdeal,
  condOk, matchChain, ballCandidates, ballTrack, analyzeBlock, fill, evalRules, watchMsg, validateCfg, mergeCfg, sentence };
if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.PadelLogic = API;
})(typeof window !== 'undefined' ? window : globalThis);
