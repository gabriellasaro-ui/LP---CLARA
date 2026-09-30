"""Pesquisa de experiência (NPS) do evento.

Copy das perguntas herdada da pesquisa da LP V4 Minas, adaptada só onde o
público muda (lá era "empresário", aqui "dono de restaurante").

Tabela própria. O painel de admin ganha a aba "NPS".
"""

import csv
import io
import os
import re
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from flask import Blueprint, Response, jsonify, render_template, request, session

bp = Blueprint("nps", __name__, url_prefix="/nps")

CABECALHO = {
    "eyebrow": "Pesquisa de experiência",
    "titulo": "Como foi sua experiência no encontro?",
    "subtitulo": "Cozinha Campeã × V4 Company · TV Sim · Belo Horizonte",
    "micro": "Leva menos de 2 minutos. Sua resposta ajuda a construir os próximos encontros.",
}

# As quatro notas de 0 a 10.
PERGUNTAS = [
    {
        "id": "recomendacao",
        "bloco": "Recomendação",
        "texto": "Em uma escala de 0 a 10, o quanto você recomendaria este encontro "
                 "para outro dono de restaurante?",
        "min": "0 · Nada provável",
        "max": "10 · Extremamente provável",
    },
    {
        "id": "conteudo",
        "bloco": "Conteúdo",
        "texto": "Que nota você dá para o conteúdo da palestra e do diagnóstico ao vivo?",
        "min": "0 · Péssimo",
        "max": "10 · Excelente",
    },
    {
        "id": "networking",
        "bloco": "Networking",
        "texto": "Que nota você dá para as conexões e o networking da noite?",
        "min": "0 · Péssimo",
        "max": "10 · Excelente",
    },
    {
        "id": "organizacao",
        "bloco": "Organização",
        "texto": "Que nota você dá para a organização do encontro — recepção, ritmo, "
                 "estrutura e acompanhamento?",
        "min": "0 · Péssimo",
        "max": "10 · Excelente",
    },
]
IDS = [p["id"] for p in PERGUNTAS]
NOMES = {p["id"]: p["bloco"] for p in PERGUNTAS}

# --------------------------------------------------------------------------- #
# Banco
# --------------------------------------------------------------------------- #

DB_SCHEMA = os.environ.get("DIAG_SCHEMA", "dashboard_tvsim")
DB_TABELA = os.environ.get("NPS_TABELA", "nps_respostas")

_IDENTIFICADOR = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
for _nome in (DB_SCHEMA, DB_TABELA):
    if not _IDENTIFICADOR.match(_nome):
        raise RuntimeError(f"DIAG_SCHEMA/NPS_TABELA inválido: {_nome!r}")

TABELA = f"{DB_SCHEMA}.{DB_TABELA}"

SCHEMA = f"""
CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};
CREATE TABLE IF NOT EXISTS {TABELA} (
    id                SERIAL PRIMARY KEY,
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT now(),
    nome              TEXT        NOT NULL,
    email             TEXT        NOT NULL,
    telefone          TEXT        NOT NULL,
    restaurante       TEXT        NOT NULL,
    recomendacao      SMALLINT    NOT NULL,
    conteudo          SMALLINT    NOT NULL,
    networking        SMALLINT    NOT NULL,
    organizacao       SMALLINT    NOT NULL,
    observacoes       TEXT,
    proximos_eventos  BOOLEAN     NOT NULL DEFAULT false
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
# Cálculo do NPS
# --------------------------------------------------------------------------- #

def classificar(nota):
    """Faixas clássicas do NPS."""
    if nota >= 9:
        return "promotor"
    if nota >= 7:
        return "neutro"
    return "detrator"


def calcular_nps(notas):
    """NPS = % promotores - % detratores, arredondado para inteiro."""
    if not notas:
        return 0, {"promotor": 0, "neutro": 0, "detrator": 0}
    contagem = {"promotor": 0, "neutro": 0, "detrator": 0}
    for n in notas:
        contagem[classificar(n)] += 1
    total = len(notas)
    nps = (contagem["promotor"] - contagem["detrator"]) * 100 / total
    return round(nps), contagem


# --------------------------------------------------------------------------- #
# Rotas públicas
# --------------------------------------------------------------------------- #

@bp.route("/", methods=["GET"], strict_slashes=False)
def pagina():
    return render_template(
        "nps.html",
        cabecalho=CABECALHO,
        perguntas=PERGUNTAS,
        ja_enviou=bool(session.get("nps_enviado")),
    )


@bp.route("/novo", methods=["GET"], strict_slashes=False)
def novo():
    session.pop("nps_enviado", None)
    return pagina()


@bp.route("/api/responder", methods=["POST"])
def responder():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip()
    telefone = (dados.get("telefone") or "").strip()
    restaurante = (dados.get("restaurante") or "").strip()
    observacoes = (dados.get("observacoes") or "").strip()
    proximos = bool(dados.get("proximos_eventos"))

    if len(nome) < 2:
        return jsonify({"erro": "Informe seu nome."}), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"erro": "Informe um e-mail válido."}), 400
    if len(re.sub(r"\D", "", telefone)) < 10:
        return jsonify({"erro": "Informe um telefone com DDD."}), 400
    if len(restaurante) < 2:
        return jsonify({"erro": "Informe o nome do seu negócio."}), 400

    notas = {}
    for p in PERGUNTAS:
        valor = dados.get(p["id"])
        if not isinstance(valor, int) or not 0 <= valor <= 10:
            return jsonify({"erro": f"Falta a nota de “{p['bloco']}”."}), 400
        notas[p["id"]] = valor

    with conectar() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {TABELA} (nome, email, telefone, restaurante, recomendacao, "
            " conteudo, networking, organizacao, observacoes, proximos_eventos) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (nome, email, telefone, restaurante, notas["recomendacao"],
             notas["conteudo"], notas["networking"], notas["organizacao"],
             observacoes or None, proximos),
        )

    session["nps_enviado"] = True
    return jsonify({
        "ok": True,
        "classificacao": classificar(notas["recomendacao"]),
        "proximos_eventos": proximos,
    })


# --------------------------------------------------------------------------- #
# Admin (mesma sessão do painel do diagnóstico)
# --------------------------------------------------------------------------- #

@bp.route("/api/lista", methods=["GET"])
def lista():
    if not session.get("diag_admin"):
        return jsonify({"erro": "não autorizado"}), 403

    with conectar() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, criado_em, nome, email, telefone, restaurante, recomendacao, "
                "conteudo, networking, organizacao, observacoes, proximos_eventos "
                f"FROM {TABELA} ORDER BY criado_em DESC"
            )
            linhas = cur.fetchall()

    total = len(linhas)
    nps, contagem = calcular_nps([l["recomendacao"] for l in linhas])

    medias = []
    for p in PERGUNTAS:
        valores = [l[p["id"]] for l in linhas]
        medias.append({
            "id": p["id"],
            "nome": p["bloco"],
            "media": round(sum(valores) / len(valores), 1) if valores else 0.0,
        })

    querem_proximos = sum(1 for l in linhas if l["proximos_eventos"])

    return jsonify({
        "total": total,
        "nps": nps,
        "promotores": contagem["promotor"],
        "neutros": contagem["neutro"],
        "detratores": contagem["detrator"],
        "medias": medias,
        "querem_proximos": querem_proximos,
        "pessoas": [
            {
                "id": l["id"],
                "quando": l["criado_em"].strftime("%d/%m %H:%M"),
                "nome": l["nome"],
                "restaurante": l["restaurante"],
                "email": l["email"],
                "telefone": l["telefone"],
                "whatsapp": re.sub(r"\D", "", l["telefone"] or ""),
                "notas": {p["id"]: l[p["id"]] for p in PERGUNTAS},
                "recomendacao": l["recomendacao"],
                "classificacao": classificar(l["recomendacao"]),
                "observacoes": l["observacoes"] or "",
                "proximos_eventos": l["proximos_eventos"],
            }
            for l in linhas
        ],
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    })


@bp.route("/admin/export.csv", methods=["GET"])
def export_csv():
    if not session.get("diag_admin"):
        return jsonify({"erro": "não autorizado"}), 403

    with conectar() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {TABELA} ORDER BY criado_em")
            linhas = cur.fetchall()

    buf = io.StringIO()
    escritor = csv.writer(buf, delimiter=";")
    escritor.writerow(
        ["Data", "Nome", "Negócio", "E-mail", "Telefone"]
        + [p["bloco"] for p in PERGUNTAS]
        + ["Classificação", "Quer próximos eventos", "Observações"]
    )
    for l in linhas:
        escritor.writerow(
            [l["criado_em"].strftime("%d/%m/%Y %H:%M"), l["nome"], l["restaurante"],
             l["email"], l["telefone"]]
            + [l[p["id"]] for p in PERGUNTAS]
            + [classificar(l["recomendacao"]),
               "sim" if l["proximos_eventos"] else "não",
               (l["observacoes"] or "").replace("\n", " ")]
        )

    return Response(
        "﻿" + buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=nps-cozinha-campea.csv"},
    )
