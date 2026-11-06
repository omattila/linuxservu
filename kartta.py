import os, re, json, sqlite3, ipaddress, urllib.request
from collections import defaultdict
from flask import Blueprint, jsonify, render_template_string

LOG = "/var/log/nginx/access.log"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kartta.db")
bp = Blueprint("kartta", __name__, url_prefix="/kartta")
RIVI = re.compile(r'^(\S+) ')


def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS geo (
        ip TEXT PRIMARY KEY, lat REAL, lon REAL, city TEXT, country TEXT, ok INTEGER)""")
    return c


def lue_ipt():
    laskuri = defaultdict(int)
    try:
        with open(LOG, "rb") as f:
            f.seek(0, 2)
            koko = f.tell()
            f.seek(max(0, koko - 2_000_000))
            data = f.read().decode("utf-8", "ignore").splitlines()
    except (PermissionError, FileNotFoundError):
        return None
    for rivi in data:
        m = RIVI.match(rivi)
        if not m:
            continue
        ip = m.group(1)
        try:
            a = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if a.is_private or a.is_loopback:
            continue
        laskuri[ip] += 1
    return laskuri


def hae_sijainnit(ipt, c):
    puuttuu = [ip for ip in ipt if not c.execute("SELECT 1 FROM geo WHERE ip=?", (ip,)).fetchone()]
    for i in range(0, min(len(puuttuu), 100), 100):
        erä = puuttuu[i:i + 100]
        try:
            req = urllib.request.Request(
                "http://ip-api.com/batch?fields=status,country,city,lat,lon,query",
                data=json.dumps(erä).encode(), headers={"Content-Type": "application/json"})
            vast = json.loads(urllib.request.urlopen(req, timeout=5).read())
        except Exception:
            return
        for r in vast:
            if r.get("status") == "success":
                c.execute("INSERT OR REPLACE INTO geo VALUES (?,?,?,?,?,1)",
                          (r["query"], r["lat"], r["lon"], r.get("city", ""), r.get("country", "")))
            else:
                c.execute("INSERT OR REPLACE INTO geo VALUES (?,0,0,'','',0)", (r["query"],))
        c.commit()


@bp.route("/api")
def api():
    ipt = lue_ipt()
    if ipt is None:
        return jsonify(virhe="Lokia ei voi lukea. Aja: sudo usermod -aG adm ubuntu"), 500
    c = db()
    hae_sijainnit(ipt, c)
    paikat = defaultdict(lambda: {"n": 0})
    yht = 0
    for ip, n in ipt.items():
        r = c.execute("SELECT lat,lon,city,country,ok FROM geo WHERE ip=?", (ip,)).fetchone()
        if not r or not r[4]:
            continue
        avain = (round(r[0], 1), round(r[1], 1))
        p = paikat[avain]
        p.update(lat=r[0], lon=r[1], city=r[2], country=r[3])
        p["n"] += n
        yht += n
    c.close()
    return jsonify(paikat=list(paikat.values()), kaynnit=yht, vierailijat=len(ipt))


SIVU = r"""<!doctype html><html lang="fi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Vierailijakartta</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
 body{margin:0;background:#0d1117;color:#e6edf3;font-family:sans-serif}
 header{padding:16px 20px;display:flex;gap:30px;align-items:baseline;flex-wrap:wrap}
 h1{margin:0;font-size:1.4em;color:#60a5fa} .luku{font-family:monospace;color:#00ff9c;font-size:1.3em}
 #kartta{height:calc(100vh - 70px)}
 .leaflet-tile{filter:invert(1) hue-rotate(180deg) brightness(.9) contrast(.9)}
 #virhe{color:#f87171;padding:0 20px}
</style></head><body>
<header><h1>Vierailijakartta</h1>
 <div>Käyntejä <span class="luku" id="k">-</span></div>
 <div>Vierailijoita <span class="luku" id="v">-</span></div></header>
<div id="virhe"></div><div id="kartta"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
 var kartta = L.map('kartta', {worldCopyJump:true}).setView([30, 10], 2);
 L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
   {attribution:'&copy; OpenStreetMap', maxZoom:12}).addTo(kartta);
 var ryhma = L.layerGroup().addTo(kartta);
 function paivita(){
  fetch('/kartta/api').then(r=>r.json()).then(d=>{
   if(d.virhe){document.getElementById('virhe').textContent=d.virhe;return;}
   document.getElementById('virhe').textContent='';
   document.getElementById('k').textContent=d.kaynnit;
   document.getElementById('v').textContent=d.vierailijat;
   ryhma.clearLayers();
   d.paikat.forEach(p=>{
    L.circleMarker([p.lat,p.lon],{radius:6+Math.sqrt(p.n)*2,color:'#00ff9c',
      fillColor:'#00ff9c',fillOpacity:.35,weight:2})
     .bindTooltip((p.city||'?')+', '+p.country+' · '+p.n+' käyntiä').addTo(ryhma);
   });
  });
 }
 paivita(); setInterval(paivita, 30000);
</script></body></html>"""


@bp.route("/")
def index():
    return render_template_string(SIVU)
