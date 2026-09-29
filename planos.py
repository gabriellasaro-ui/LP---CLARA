"""Página de captura dos planos: nome, e-mail, telefone e plano desejado.

Tabela propria, separada do diagnostico. O painel de admin ganha uma aba que
lista quem demonstrou interesse, reaproveitando a mesma sessao de admin.
"""

import csv
import io
import os
import re
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from flask import Blueprint, Response, jsonify, render_template, request, session

bp = Blueprint("planos", __name__, url_prefix="/planos")

# Escassez é mensagem de página, não trava: ninguém fica de fora por causa de
# um contador, e a página nunca anuncia quantas pessoas já se inscreveram.
ESCASSEZ = "Somente 10 vagas para este ciclo"

OFERTA = [
    {
        "id": "basic",
        "etiqueta": "Para começar",
        "nome": "Basic",
        "preco": "R$ 4.795",
        "valor": 4795,
        "periodo": "/mês · 6 meses",
        "destaque": False,
        "itens": [
            "Gravação padronizada no Cozinha Campeã",
            "12 posts por mês nas redes sociais",
            "Back bus: 5 ônibus por 3 meses",
        ],
    },
    {
        "id": "intermediario",
        "etiqueta": "Recomendado",
        "nome": "Intermediário",
        "preco": "R$ 6.195",
        "valor": 6195,
        "periodo": "/mês · 6 meses",
        "destaque": True,
        "itens": [
            "Gravação personalizada no perfil da Clara",
            "20 posts por mês nas redes sociais",
            "Back bus: 5 ônibus por 6 meses",
            "Dashboard de resultados",
        ],
    },
    {
        "id": "avancado",
        "etiqueta": "Para crescer",
        "nome": "Avançado",
        "preco": "R$ 7.595",
        "valor": 7595,
        "periodo": "/mês · 6 meses",
        "destaque": False,
        "itens": [
            "Gravação no restaurante (reels + stories)",
            "30 posts por mês nas redes sociais",
            "Back bus: 10 ônibus por 6 meses",
            "Dashboard de resultados",
        ],
    },
    {
        "id": "enterprise",
        "etiqueta": "Personalizado",
        "nome": "Enterprise",
        "preco": "Sob medida",
        "valor": None,
        "periodo": "proposta personalizada",
        "destaque": False,
        "itens": [
            "Tudo do plano Avançado",
            "Sistema de gestão PDV",
            "Gestão de iFood (em breve)",
            "Gestão de LinkedIn (em breve)",
        ],
    },
]

INCLUSO = ("Em todos os planos: gestão de tráfego pago, estratégia de marketing, "
           "experiência no festival e gravações em collab com o Cozinha Campeã.")

NOMES_PLANO = {p["id"]: p["nome"] for p in OFERTA}
VALOR_PLANO = {p["nome"]: p["valor"] for p in OFERTA}

# --------------------------------------------------------------------------- #
# Banco
# --------------------------------------------------------------------------- #

DB_SCHEMA = os.environ.get("DIAG_SCHEMA", "dashboard_tvsim")
DB_TABELA = os.environ.get("PLANOS_TABELA", "interesse_planos")

_IDENTIFICADOR = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
for _nome in (DB_SCHEMA, DB_TABELA):
    if not _IDENTIFICADOR.match(_nome):
        raise RuntimeError(f"DIAG_SCHEMA/PLANOS_TABELA inválido: {_nome!r}")

TABELA = f"{DB_SCHEMA}.{DB_TABELA}"

SCHEMA = f"""
CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};
CREATE TABLE IF NOT EXISTS {TABELA} (
    id          SERIAL PRIMARY KEY,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    nome        TEXT        NOT NULL,
    email       TEXT        NOT NULL,
    telefone    TEXT        NOT NULL,
    plano       TEXT        NOT NULL,
    restaurante TEXT
);
CREATE INDEX IF NOT EXISTS idx_{DB_TABELA}_criado_em ON {TABELA} (criado_em DESC);
"""


def conectar():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não definida (crie o arquivo .env).")
    return psycopg2.connect(url, connect_timeout=10)


def init_db():
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA)


# --------------------------------------------------------------------------- #
# Rotas públicas
# --------------------------------------------------------------------------- #

@bp.route("/", methods=["GET"], strict_slashes=False)
def pagina():
    return render_template(
        "planos.html",
        oferta=OFERTA,
        incluso=INCLUSO,
        escassez=ESCASSEZ,
        ja_enviou=bool(session.get("planos_enviado")),
    )


@bp.route("/api/interesse", methods=["POST"])
def interesse():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip()
    telefone = (dados.get("telefone") or "").strip()
    restaurante = (dados.get("restaurante") or "").strip()
    plano = (dados.get("plano") or "").strip()

    if len(nome) < 2:
        return jsonify({"erro": "Informe seu nome."}), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"erro": "Informe um e-mail válido."}), 400
    if len(re.sub(r"\D", "", telefone)) < 10:
        return jsonify({"erro": "Informe um telefone com DDD."}), 400
    if plano not in NOMES_PLANO:
        return jsonify({"erro": "Escolha um plano."}), 400

    with conectar() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {TABELA} (nome, email, telefone, plano, restaurante) "
            "VALUES (%s,%s,%s,%s,%s)",
            (nome, email, telefone, NOMES_PLANO[plano], restaurante or None),
        )

    session["planos_enviado"] = True
    return jsonify({"ok": True, "plano": NOMES_PLANO[plano]})


# --------------------------------------------------------------------------- #
# Admin (usa a mesma sessão do painel do diagnóstico)
# --------------------------------------------------------------------------- #

@bp.route("/api/lista", methods=["GET"])
def lista():
    if not session.get("diag_admin"):
        return jsonify({"erro": "não autorizado"}), 403

    with conectar() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, criado_em, nome, email, telefone, plano, restaurante "
                f"FROM {TABELA} ORDER BY criado_em DESC"
            )
            linhas = cur.fetchall()

    por_plano = []
    for p in OFERTA:
        n = sum(1 for l in linhas if l["plano"] == p["nome"])
        por_plano.append({"nome": p["nome"], "n": n, "valor": p["valor"]})

    # potencial mensal: Enterprise nao entra na conta (proposta sob medida)
    potencial = sum(
        VALOR_PLANO.get(l["plano"]) or 0 for l in linhas
    )
    sob_medida = sum(1 for l in linhas if not VALOR_PLANO.get(l["plano"]))

    agora = datetime.now(timezone.utc)
    return jsonify({
        "total": len(linhas),
        "por_plano": por_plano,
        "potencial_mes": potencial,
        "sob_medida": sob_medida,
        "pessoas": [
            {
                "id": l["id"],
                "quando": l["criado_em"].strftime("%d/%m %H:%M"),
                # marca quem chegou na última hora, para o time atacar primeiro
                "novo": (agora - l["criado_em"]).total_seconds() < 3600,
                "nome": l["nome"],
                "email": l["email"],
                "telefone": l["telefone"],
                "whatsapp": re.sub(r"\D", "", l["telefone"] or ""),
                "plano": l["plano"],
                "valor": VALOR_PLANO.get(l["plano"]),
                "restaurante": l["restaurante"] or "",
            }
            for l in linhas
        ],
        "atualizado_em": agora.isoformat(),
    })


@bp.route("/admin/export.csv", methods=["GET"])
def export_csv():
    if not session.get("diag_admin"):
        return jsonify({"erro": "não autorizado"}), 403

    with conectar() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT criado_em, nome, email, telefone, plano, restaurante "
                f"FROM {TABELA} ORDER BY criado_em"
            )
            linhas = cur.fetchall()

    buf = io.StringIO()
    escritor = csv.writer(buf, delimiter=";")
    escritor.writerow(["Data", "Nome", "E-mail", "Telefone", "Plano", "Restaurante"])
    for l in linhas:
        escritor.writerow([
            l["criado_em"].strftime("%d/%m/%Y %H:%M"),
            l["nome"], l["email"], l["telefone"], l["plano"], l["restaurante"] or "",
        ])

    return Response(
        "﻿" + buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=interesse-planos.csv"},
    )
