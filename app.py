from flask import Flask, render_template, abort
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

import diagnostico
import nps
import planos

app = Flask(__name__)

# Sem chave fixa no codigo: o repositorio e publico e uma constante aqui deixaria
# qualquer um forjar a sessao de admin. Sem SECRET_KEY no ambiente, sorteia uma
# chave por processo — as sessoes caem a cada reinicio, o que e o aviso de que
# a variavel precisa ser configurada.
_chave = os.environ.get("SECRET_KEY")
if not _chave:
    _chave = secrets.token_urlsafe(48)
    print("[diagnostico] AVISO: SECRET_KEY nao definida; usando chave temporaria. "
          "Defina SECRET_KEY no ambiente para as sessoes sobreviverem a reinicios.")
app.secret_key = _chave

# Evita cache de template e de arquivos estaticos (CSS/imagens) durante o desenvolvimento
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.jinja_env.auto_reload = True

app.register_blueprint(diagnostico.bp)
app.register_blueprint(planos.bp)
app.register_blueprint(nps.bp)

# Roda na importacao para valer tambem sob gunicorn (o bloco __main__ nao executa la).
# Se o banco estiver fora do ar, a LP continua servindo normalmente.
for _modulo, _rotulo in ((diagnostico, "diagnostico"), (planos, "planos"), (nps, "nps")):
    try:
        _modulo.init_db()
        print(f"[{_rotulo}] tabela verificada/criada com sucesso")
    except Exception as e:
        print(f"[{_rotulo}] AVISO: nao foi possivel preparar o banco: {e}")

# Slugs reservados: nao podem cair na rota curinga das landing pages
SLUGS_RESERVADOS = {"diagnostico", "planos", "nps", "static"}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/<slug>")
def lp(slug):
    if slug in SLUGS_RESERVADOS:
        abort(404)
    path = os.path.join("templates", f"{slug}.html")
    if not os.path.exists(path):
        abort(404)
    return render_template(f"{slug}.html")


@app.route("/lp/help")
def list_slugs():
    slug_list = [f for f in os.listdir("templates") if f.endswith(".html")]
    return {str(i): f.replace(".html", "") for i, f in enumerate(slug_list)}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5016, debug=False)
