import re
BAD=re.compile(r"\b(immer|nie|niemals|komplett|ausschließlich|keineswegs|garantiert)\b",re.I)
PH=["du denkst","weißt du","was meinst du","ganz einfach","absolut","enorm","massiv"]
def check(d):
    e=[]
    for i,(em,tx) in enumerate(d["cards"],1):
        w=len(tx.split())
        if not 25<=w<=45: e.append(f"{d['id']} K{i}: {w} Wörter")
        if len(tx)>280: e.append(f"{d['id']} K{i}: {len(tx)} Zeichen")
        if re.search(r"[–—]",tx) or "!" in tx: e.append(f"{d['id']} K{i}: Strich/!")
        if any(p in tx.lower() for p in PH): e.append(f"{d['id']} K{i}: Phrase")
        if i<=4 and not tx.rstrip().endswith("?"): e.append(f"{d['id']} K{i}: kein ?")
        if i==5 and tx.rstrip().endswith("?"): e.append(f"{d['id']} K5: Frage")
    nums=[q[4] for q in d["quiz"]]
    if len(set(nums))!=3: e.append(d["id"]+": Kartennummern doppelt")
    for k,q in enumerate(d["quiz"],1):
        L=[len(x) for x in q[1:4]]
        if any(BAD.search(x) for x in q[2:4]): e.append(f"{d['id']} Q{k}: Extremwort")
        if L[0]>1.5*max(L[1:]) or max(L)>2.0*min(L): e.append(f"{d['id']} Q{k}: Länge {L}")
        if re.search(r"[–—]","".join(q[:4])): e.append(f"{d['id']} Q{k}: Strich")
    if len(d["s"])>14: e.append(d["id"]+": s zu lang")
    if not re.match(r"^[a-z0-9_]{2,20}$",d["id"]): e.append("id")
    return e
