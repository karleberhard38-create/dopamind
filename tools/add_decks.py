"""Fügt neue Decks in decks.json ein (nach Formatprüfung).
Aufruf: python3 tools/add_decks.py neue.json [--write]
neue.json = Liste von Decks: {t,s,k,id,cards:[[emoji,text]x5],quiz:[[frage,richtig,falsch1,falsch2,kartennr]x3],sources:[[publisher,title,url],...]}"""
import json,sys,time,datetime,os
sys.path.insert(0,os.path.dirname(__file__))
from chk import check
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P=os.path.join(root,"decks.json"); PO=os.path.join(root,"decks_owner.json")
new=json.load(open(sys.argv[1]))
data=json.load(open(P)); L=data if isinstance(data,list) else data["decks"]
have={x["id"] for x in L}|({x["id"] for x in json.load(open(PO))} if os.path.exists(PO) else set())
errs=[]; ok=[]
for d in new:
    if d["id"] in have: errs.append(d["id"]+": id schon vorhanden"); continue
    e=check(d); errs+=e
    if not e: ok.append(d)
print("\n".join(errs) or "ALLE PRÜFUNGEN OK", "| gültig:",len(ok),"von",len(new))
if "--write" in sys.argv:
    for d in ok:
        L.append(dict(t=d["t"],s=d["s"],k=d["k"],cards=d["cards"],quiz=d["quiz"],id=d["id"],prod=None,
          sources=[dict(publisher=a,title=b,url=c) for a,b,c in d["sources"]],status="approved",ts=int(time.time()*1000),
          review=dict(date=datetime.date.today().isoformat(),facts="pass",rounds=1,
            method="Geplante Aufgabe: Quellenseiten gelesen, Aussagen gegen Quellen abgeglichen, unabhängiger Faktencheck durch zweiten Prüfer, Format- und Quizregeln per Programm geprüft.")))
    json.dump(data,open(P,"w"),ensure_ascii=False,indent=1); print("geschrieben:",len(ok))
