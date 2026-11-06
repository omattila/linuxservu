from flask import Flask, render_template_string, render_template
import os
import pymysql

app = Flask(__name__)
import kartta
app.register_blueprint(kartta.bp)

def kasvata(sivu):
    db = pymysql.connect(
        host="localhost",
        user="flask",
	password="Salasana123!",
        database="viikko2"
    )

    cur = db.cursor()

    cur.execute(
        "UPDATE laskuri SET kaynnit = kaynnit + 1 WHERE id = 1"
    )

    db.commit()

    cur.execute(
        "SELECT kaynnit FROM laskuri WHERE id = 1"
    )

    maara = cur.fetchone()[0]

    cur.close()
    db.close()

    return maara
POHJA = """<!DOCTYPE html>
<html lang="fi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ otsikko }}</title>
  <style>
    body { background: #111; color: white; font-family: sans-serif; padding: 20px 20px 20px 80px; }
    h1, h2 { color: #60a5fa; }
    p { color: #ffffff; }
    pre { background: transparent; color: white; padding: 16px; overflow-x: auto; }
    .hamppari {
      position: fixed; top: 10px; left: 10px;
      font-size: 32px; background: #333; color: white;
      border: none; padding: 5px 14px; cursor: pointer; z-index: 1000;
    }
    .valikko {
      display: none; position: fixed; top: 60px; left: 10px;
      background: #333; padding: 10px; z-index: 1000;
    }
    .valikko a {
      display: block; color: white; padding: 10px 20px;
      text-decoration: none; font-size: 18px;
    }
    .valikko a:hover { background: #555; }
    .valikko.nayta { display: block; }
  </style>
</head>
<body>
  <button class="hamppari" onclick="document.getElementById('valikko').classList.toggle('nayta')">&#9776;</button>
  <div class="valikko" id="valikko">
    <a href="/">Etusivu</a>
    <a href="/viikko2/">Viikko 2</a>
  </div>

  {{ sisalto|safe }}

  <hr>
  <p>Vierailijoita tällä sivulla: {{ maara }}</p>
</body>
</html>"""

ETUSIVU = """
  <h1>Oliver's Linux Server</h1>
  <p>Welcome to my Week 1 project!</p>

  <h2>1. Which Linux distribution and version did you install?</h2>
  <p>Ubuntu26-26.04</p>

  <h2>2. What is Nginx, and what does it do on your server?</h2>
  <p>Nginx is web server software. It listens for requests from web browsers and delivers website content to visitors. On this server Nginx hosts my website and makes it available through the network.</p>

  <h2>3.Commands that i used</h2>

  <pre>sudo apt update
# Updates package information

sudo apt install nginx -y
# Installs Nginx

systemctl status nginx
# Checks if Nginx is running

sudo systemctl enable nginx
# Starts Nginx automatically after reboot

sudo systemctl restart nginx
# Restarts Nginx</pre>
"""

VIIKKO2 = """
  <h1>Viikko 2</h1>
  <p>Tämä sivu on tehty Flaskilla.</p>

  <h2>Kello</h2>
  <div id="kello" style="font-size: 3em; font-family: monospace; color: #00f9c;">--:--:--</div>
  <div id="paiva" style="font-size: 1.2em; color: #ffffff;"></div>

  <script>
    function paivitaKello() {
      var nyt = new Date();
      document.getElementById('kello').textContent = nyt.toLocaleTimeString('fi-FI');
      document.getElementById('paiva').textContent = nyt.toLocaleDateString('fi-FI');
    }
    setInterval(paivitaKello, 1000);
    paivitaKello();
  </script>
"""

@app.route("/")
def etusivu():
    return render_template_string(POHJA, otsikko="Etusivu", sisalto=ETUSIVU, maara=kasvata("etusivu"))

@app.route("/viikko2/")
def viikko2():
   return render_template("viikko2.html", maara=kasvata("viikko2"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
