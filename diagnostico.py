"""Diagnostico Cozinha Campea: formulario do evento + painel ao vivo.

Estrutura (conforme o artefato do diagnostico):
  - 4 perguntas de perfil, sem pontuacao, que alimentam os filtros do painel;
  - 20 perguntas pontuadas de 0 a 3 (A=0, B=1, C=2, D=3), 5 em cada pilar;
  - contato no fim (nome, restaurante, WhatsApp) com aceite explicito de LGPD.
    O resultado aparece mesmo para quem nao aceita ser contatado.

Rotas: /diagnostico (aberto) e /diagnostico/admin (senha).
"""

import csv
import io
import json
import os
import re
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from flask import (
    Blueprint, Response, jsonify, redirect, render_template, request, session, url_for
)

bp = Blueprint("diagnostico", __name__, url_prefix="/diagnostico")

NOTA_MAXIMA = 3          # cada pergunta vale de 0 a 3
POR_PILAR = 5            # perguntas em cada pilar
PONTOS_PILAR = 15        # 5 perguntas x 3
TOTAL_MAXIMO = 60        # 20 perguntas x 3

# No radar o pilar aparece de 0 a 5 = score / 20. A meta e 4, ou seja 80 pontos.
ESCALA_RADAR = 5
META_SCORE = 80
META = META_SCORE / 20   # 4.0

PILARES = [
    ("visto", "Ser visto"),
    ("desejado", "Ser desejado"),
    ("escolhido", "Ser escolhido"),
    ("lucrativo", "Ser lucrativo"),
]
PILARES_NOMES = dict(PILARES)

# Desempate do pilar mais fraco: sem margem o resto nao se sustenta.
ORDEM_DESEMPATE = ["lucrativo", "escolhido", "desejado", "visto"]

# Nivel pelo score geral (0 a 100): V0 < 40, V1 40-59, V2 60-79, V3 >= 80.
NIVEIS = [
    ("V0", "Improviso", 0),
    ("V1", "Fundação", 40),
    ("V2", "Gestão", 60),
    ("V3", "Restaurante Campeão", 80),
]
CODIGOS_NIVEL = [c for c, _, _ in NIVEIS]
NOMES_NIVEL = {c: n for c, n, _ in NIVEIS}

MENSAGENS = {
    "V0": "Seu restaurante depende do movimento e de você. O primeiro passo é enxergar "
          "os números e aparecer para quem está perto.",
    "V1": "O básico está no ar. Agora falta rotina: medir toda semana e transformar "
          "cliente de uma vez em cliente de sempre.",
    "V2": "Você já mede. O próximo salto é integrar marketing e gestão para crescer "
          "com margem, não só com movimento.",
    "V3": "Seu restaurante é visto, desejado, escolhido e lucrativo. O desafio agora é "
          "escalar sem perder o padrão.",
}

# --------------------------------------------------------------------------- #
# Perguntas de perfil (sem pontuacao)
# --------------------------------------------------------------------------- #

PERFIL = [
    {
        "id": "p1",
        "campo": "tipo_negocio",
        "pergunta": "Qual o tipo do seu negócio?",
        "opcoes": ["Restaurante", "Bar", "Cafeteria ou padaria",
                   "Hamburgueria ou pizzaria", "Delivery", "Outro"],
    },
    {
        "id": "p2",
        "campo": "faturamento",
        "pergunta": "Qual o faturamento médio mensal?",
        "opcoes": ["Até R$ 50 mil", "R$ 50 a 200 mil",
                   "R$ 200 mil a 1 milhão", "Acima de R$ 1 milhão"],
    },
    {
        "id": "p3",
        "campo": "dependencia_delivery",
        "pergunta": "Quanto do faturamento vem de aplicativos de delivery?",
        "opcoes": ["Nada", "Até 20%", "De 20% a 50%", "Mais de 50%"],
    },
    {
        "id": "p4",
        "campo": "tempo_casa",
        "pergunta": "Há quanto tempo o negócio está aberto?",
        "opcoes": ["Menos de 2 anos", "2 a 5 anos", "Mais de 5 anos"],
    },
]
PERFIL_POR_ID = {p["id"]: p for p in PERFIL}

# --------------------------------------------------------------------------- #
# 20 perguntas pontuadas. A ordem das opcoes e a pontuacao: A=0, B=1, C=2, D=3.
# --------------------------------------------------------------------------- #

PERGUNTAS = [
    # ------------------------------ Ser visto ------------------------------ #
    {
        "id": "V1", "pilar": "visto",
        "pergunta": "Quando alguém busca restaurante no seu bairro no Google, o seu aparece?",
        "opcoes": [
            "Não sei ou não tenho perfil no Google",
            "Tenho perfil, mas incompleto ou desatualizado",
            "Perfil completo, com fotos e horário certos",
            "Perfil completo, atualizado toda semana, e aparece entre os primeiros",
        ],
    },
    {
        "id": "V2", "pilar": "visto",
        "pergunta": "Com que frequência o restaurante publica no Instagram?",
        "opcoes": [
            "Raramente ou nunca",
            "Quando dá tempo, sem calendário",
            "Toda semana, com calendário",
            "Calendário mensal de prato, bastidor e oferta, com resultado medido",
        ],
    },
    {
        "id": "V3", "pilar": "visto",
        "pergunta": "Vocês investem em anúncios pagos?",
        "opcoes": [
            "Nunca",
            "Impulsiono posts de vez em quando",
            "Invisto todo mês com objetivo definido",
            "Invisto todo mês e sei quanto custa cada cliente ou reserva",
        ],
    },
    {
        "id": "V4", "pilar": "visto",
        "pergunta": "Vocês fazem ações com influenciadores ou parceiros?",
        "opcoes": [
            "Nunca fizemos",
            "Permuta sem objetivo definido",
            "Ações com influenciadores da região",
            "Ações com público local, medidas com cupom, link ou código",
        ],
    },
    {
        "id": "V5", "pilar": "visto",
        "pergunta": "Você sabe como os clientes novos conheceram o restaurante?",
        "opcoes": [
            "Não faço ideia",
            "Tenho uma noção pelas conversas",
            "Pergunto e anoto às vezes",
            "Registro a origem de todo cliente novo",
        ],
    },
    # ---------------------------- Ser desejado ----------------------------- #
    {
        "id": "D1", "pilar": "desejado",
        "pergunta": "Qual a nota do restaurante no Google?",
        "opcoes": [
            "Não sei, ou abaixo de 4,0",
            "De 4,0 a 4,4",
            "De 4,5 a 4,7",
            "4,8 ou mais",
        ],
    },
    {
        "id": "D2", "pilar": "desejado",
        "pergunta": "Quantas avaliações novas chegam por mês?",
        "opcoes": [
            "Não sei, ou quase nenhuma",
            "Até 10",
            "De 11 a 50",
            "Mais de 50",
        ],
    },
    {
        "id": "D3", "pilar": "desejado",
        "pergunta": "Vocês respondem as avaliações?",
        "opcoes": [
            "Não respondemos",
            "Só as negativas, quando dá",
            "A maioria, em até uma semana",
            "Todas, em até 48 horas, com padrão de resposta",
        ],
    },
    {
        "id": "D4", "pilar": "desejado",
        "pergunta": "O seu restaurante tem um posicionamento claro?",
        "opcoes": [
            "Não saberia dizer em uma frase",
            "“Comida boa e bom atendimento”",
            "Temos uma frase clara, mas o cliente não repete",
            "Frase clara que aparece no perfil, no salão e nas avaliações",
        ],
    },
    {
        "id": "D5", "pilar": "desejado",
        "pergunta": "O perfil no Instagram leva o cliente à ação?",
        "opcoes": [
            "Sem endereço, cardápio ou link",
            "Tem parte das informações",
            "Bio com oferta, endereço, cardápio e link de reserva ou pedido",
            "Tudo isso, e sabemos quantas reservas ou pedidos vêm do perfil",
        ],
    },
    # ---------------------------- Ser escolhido ---------------------------- #
    {
        "id": "E1", "pilar": "escolhido",
        "pergunta": "Você sabe quantos clientes voltam?",
        "opcoes": [
            "Não",
            "Tenho uma noção",
            "Sei de parte deles, por reserva ou programa",
            "Acompanho a taxa de retorno todo mês",
        ],
    },
    {
        "id": "E2", "pilar": "escolhido",
        "pergunta": "Vocês têm uma base própria de clientes?",
        "opcoes": [
            "Não temos o contato dos clientes",
            "Alguns contatos, sem uso",
            "Base no WhatsApp, com mensagens de vez em quando",
            "Base organizada, com ação de recompra todo mês",
        ],
    },
    {
        "id": "E3", "pilar": "escolhido",
        "pergunta": "Como está a dependência do aplicativo?",
        "opcoes": [
            "A maior parte vem do app e não temos canal próprio",
            "Temos canal próprio, mas quase ninguém usa",
            "Canal próprio funcionando, com preço diferente do app",
            "O canal próprio é o principal para quem já é cliente",
        ],
    },
    {
        "id": "E4", "pilar": "escolhido",
        "pergunta": "Como é o padrão de atendimento?",
        "opcoes": [
            "Cada um atende do seu jeito",
            "Orientações verbais",
            "Padrão escrito e treinamento na entrada",
            "Padrão escrito, treinamento contínuo e checagem por cliente oculto ou avaliação",
        ],
    },
    {
        "id": "E5", "pilar": "escolhido",
        "pergunta": "Como vocês planejam datas e campanhas?",
        "opcoes": [
            "Não planejamos",
            "Pensamos na semana da data",
            "Planejamos com um mês de antecedência",
            "Calendário anual com datas, eventos e metas",
        ],
    },
    # ---------------------------- Ser lucrativo ---------------------------- #
    {
        "id": "L1", "pilar": "lucrativo",
        "pergunta": "Você sabe o lucro do mês passado?",
        "opcoes": [
            "Não",
            "Sei o faturamento, não o lucro",
            "Sei o lucro, com algum atraso",
            "Fecho o resultado do mês até o dia 10",
        ],
    },
    {
        "id": "L2", "pilar": "lucrativo",
        "pergunta": "Os pratos têm ficha técnica?",
        "opcoes": [
            "Não temos",
            "Em alguns pratos",
            "Em todos, mas desatualizada",
            "Em todos, atualizada com o preço dos insumos",
        ],
    },
    {
        "id": "L3", "pilar": "lucrativo",
        "pergunta": "Vocês acompanham o CMV?",
        "opcoes": [
            "Não acompanhamos",
            "Tenho uma noção do geral",
            "Acompanho o CMV geral todo mês",
            "Acompanho o CMV por prato e uso para decidir cardápio e preço",
        ],
    },
    {
        "id": "L4", "pilar": "lucrativo",
        "pergunta": "Existe uma rotina de olhar os números?",
        "opcoes": [
            "Não temos",
            "Olho quando lembro",
            "Olho os números toda semana",
            "Reunião semanal com a equipe, olhando metas e indicadores",
        ],
    },
    {
        "id": "L5", "pilar": "lucrativo",
        "pergunta": "Como são as metas do restaurante?",
        "opcoes": [
            "Não temos metas",
            "Uma meta geral de faturamento",
            "Metas mensais, acompanhadas",
            "Metas por canal e turno, e sei a margem de cada canal",
        ],
    },
]
PERGUNTAS_POR_ID = {p["id"]: p for p in PERGUNTAS}

# --------------------------------------------------------------------------- #
# Plano de acao de 90 dias, por nivel. Cada dono recebe o plano do seu nivel;
# na tela, a linha do pilar mais fraco vai para o topo e destacada.
# --------------------------------------------------------------------------- #

PLANOS = {
    "V0": {
        "titulo": "colocar o básico no ar e enxergar os números",
        "acoes": {
            "visto": [
                "Reivindicar e configurar 100% o Perfil da Empresa no Google: categoria, "
                "endereço, horário, telefone, cardápio, link de reserva ou pedido e pelo "
                "menos 20 fotos atuais de pratos, fachada e salão",
                "Instagram com 3 posts por semana (prato, bastidor, oferta) e stories "
                "todos os dias",
                "Primeiro anúncio local, com verba fixa e um objetivo só (mensagem ou "
                "rota); perguntar no caixa “como você nos conheceu?”",
            ],
            "desejado": [
                "Responder todas as avaliações pendentes, inclusive as negativas",
                "Pedir avaliação no fechamento da conta, com QR na mesa ou na comanda; "
                "meta de 10 avaliações novas por mês",
                "Bio do Instagram com o que o restaurante é, endereço, horário, cardápio "
                "e link; destaques de Cardápio, Como chegar e Avaliações",
            ],
            "escolhido": [
                "Padrão mínimo de atendimento em uma página: recepção, tempo de espera "
                "e despedida",
                "Começar a guardar o WhatsApp dos clientes, com autorização; meta dos "
                "primeiros 100 contatos",
                "Primeira mensagem de recompra para a base (prato do dia ou evento), "
                "sem desconto",
            ],
            "lucrativo": [
                "Separar as contas da empresa e da pessoa física e anotar o faturamento "
                "todo dia",
                "Ficha técnica dos 10 pratos mais vendidos e CMV de cada um",
                "Fechar o primeiro resultado do mês (receita, custos e lucro) e revisar "
                "o preço dos pratos com CMV acima de 35%",
            ],
        },
        "metas": "Metas para chegar ao V1: Perfil no Google 100% configurado; 100% das "
                 "avaliações respondidas; 10 ou mais avaliações novas por mês; bio "
                 "completa; ficha técnica dos 10 mais vendidos; lucro do mês conhecido.",
    },
    "V1": {
        "titulo": "criar rotina e medir toda semana",
        "acoes": {
            "visto": [
                "Calendário mensal de conteúdo, com 4 a 5 posts por semana: prato, "
                "bastidor, equipe, cliente e oferta",
                "Anúncios todo mês, com verba fixa e objetivo de reserva ou mensagem; "
                "acompanhar o custo por contato",
                "Primeira ação com influenciador de público local, medida por cupom ou "
                "código; registrar a origem de todo cliente novo",
            ],
            "desejado": [
                "Meta de nota média mínima de 4,5 no Google; responder todas as "
                "avaliações em até 48 horas, com padrão de resposta",
                "Meta de 30 avaliações novas por mês: equipe pedindo no fechamento e QR "
                "em todas as mesas",
                "Posicionamento em uma frase, aplicado na bio, no Google, no cardápio "
                "e no salão",
            ],
            "escolhido": [
                "Padrão de atendimento escrito e treino de 15 minutos para todo "
                "colaborador novo",
                "Base no WhatsApp separada por perfil (família, almoço, eventos), com "
                "uma ação de recompra por mês",
                "Canal próprio de reserva ou pedido, com preço diferente do app; "
                "começar a medir quantos clientes voltam",
            ],
            "lucrativo": [
                "Ficha técnica de 100% dos pratos, atualizada com o preço dos insumos",
                "CMV geral todo mês e CMV por prato dos 20 mais vendidos; destacar no "
                "cardápio os pratos que deixam mais reais",
                "Reunião de segunda com os 8 números da semana e meta mensal de "
                "faturamento e margem",
            ],
        },
        "metas": "Metas para chegar ao V2: nota média de 4,5 ou mais; 30 ou mais "
                 "avaliações novas por mês; anúncios com custo por cliente conhecido; "
                 "ficha técnica em todos os pratos; CMV mensal entre 28% e 35%; reunião "
                 "de segunda acontecendo toda semana.",
    },
    "V2": {
        "titulo": "integrar marketing e gestão para crescer com margem",
        "acoes": {
            "visto": [
                "Calendário anual de datas e campanhas (Dia das Mães, Namorados, "
                "confraternizações, 13º)",
                "Tráfego otimizado por custo por reserva ou pedido; CAC calculado "
                "por canal",
                "Influência recorrente com público local e medição por código; mais "
                "verba nos canais de menor CAC",
            ],
            "desejado": [
                "Meta de nota de 4,7 ou mais e 50 avaliações novas por mês",
                "Protocolo de crise: resposta pública em até 24 horas para críticas "
                "graves, com responsável definido",
                "Prova social no perfil (reposts de clientes, destaques de avaliações); "
                "medir reservas e pedidos que vêm do perfil",
            ],
            "escolhido": [
                "Taxa de retorno em 60 dias medida todo mês",
                "Régua de recompra no WhatsApp: aniversário e clientes 30 e 60 dias "
                "sem visita",
                "Cliente oculto a cada trimestre e checklist de padrão; meta de uma "
                "visita a mais por cliente no ano",
            ],
            "lucrativo": [
                "Resultado do mês fechado até o dia 10 e margem por canal (salão, app "
                "e canal próprio)",
                "Metas por canal e por turno; preço por canal",
                "Um único painel de marketing e gestão (CAC, retorno, CMV e margem), "
                "revisado toda semana; plano do trimestre seguinte",
            ],
        },
        "metas": "Metas para chegar ao V3: nota de 4,7 ou mais; CAC e taxa de retorno "
                 "medidos todo mês; margem por canal conhecida; protocolo de crise "
                 "pronto; painel único rodando.",
    },
    "V3": {
        "titulo": "escalar sem perder o padrão",
        "acoes": {
            "visto": [
                "Presença de marca na cidade: parcerias, eventos e mídia",
                "Testar novos públicos e canais sem passar do CAC-alvo",
                "Plano para aumentar a demanda: novo turno, evento recorrente ou "
                "delivery próprio",
            ],
            "desejado": [
                "Manter nota de 4,8 ou mais e crescer o volume de avaliações mês a mês",
                "Clientes e equipe como embaixadores no conteúdo",
                "Plano de crise de imagem documentado e treinado com a liderança",
            ],
            "escolhido": [
                "Programa de relacionamento para os clientes mais frequentes",
                "Pesquisa pós-visita para todos os clientes da base",
                "Experiência padronizada em todos os turnos, com manual e checagem",
            ],
            "lucrativo": [
                "Manuais, fichas técnicas e treinamentos prontos para replicar",
                "Sistema de gestão integrado (PDV) conectado ao painel de resultados",
                "Estudo de viabilidade de nova unidade ou nova operação, com os números "
                "do trimestre",
            ],
        },
        "metas": "Metas para manter o V3: os quatro pilares acima de 80 pontos; playbook "
                 "da operação documentado; decisão de expansão tomada com números.",
    },
}

MESES = ["Mês 1 · dias 1 a 30", "Mês 2 · dias 31 a 60", "Mês 3 · dias 61 a 90"]


def _conferir_estrutura():
    """Erra cedo se alguem editar as listas e quebrar o formato do diagnostico."""
    assert len(PERGUNTAS) == 20, f"esperadas 20 perguntas, ha {len(PERGUNTAS)}"
    for chave, nome in PILARES:
        n = sum(1 for p in PERGUNTAS if p["pilar"] == chave)
        assert n == POR_PILAR, f"{nome}: {n} perguntas (esperado {POR_PILAR})"
    for p in PERGUNTAS:
        assert len(p["opcoes"]) == 4, f"{p['id']}: {len(p['opcoes'])} opções (esperado 4)"


_conferir_estrutura()


def perguntas_publicas():
    """Formato enxuto para o front. A pontuacao nao vai junto."""
    perfil = [
        {"id": p["id"], "etapa": "Perfil do negócio",
         "pergunta": p["pergunta"], "opcoes": p["opcoes"]}
        for p in PERFIL
    ]
    pontuadas = [
        {"id": p["id"], "etapa": PILARES_NOMES[p["pilar"]],
         "pergunta": p["pergunta"], "opcoes": p["opcoes"]}
        for p in PERGUNTAS
    ]
    return perfil + pontuadas


# --------------------------------------------------------------------------- #
# Banco
# --------------------------------------------------------------------------- #

DB_SCHEMA = os.environ.get("DIAG_SCHEMA", "dashboard_tvsim")
DB_TABELA = os.environ.get("DIAG_TABELA", "diagnostico_cozinha")

_IDENTIFICADOR = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
for _nome in (DB_SCHEMA, DB_TABELA):
    if not _IDENTIFICADOR.match(_nome):
        raise RuntimeError(f"DIAG_SCHEMA/DIAG_TABELA inválido: {_nome!r}")

TABELA = f"{DB_SCHEMA}.{DB_TABELA}"

SCHEMA = f"""
CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};
CREATE TABLE IF NOT EXISTS {TABELA} (
    id                    SERIAL PRIMARY KEY,
    criado_em             TIMESTAMPTZ  NOT NULL DEFAULT now(),
    nome                  TEXT         NOT NULL,
    restaurante           TEXT         NOT NULL,
    whatsapp              TEXT,
    aceite_contato        BOOLEAN      NOT NULL DEFAULT false,
    tipo_negocio          TEXT,
    faturamento           TEXT,
    dependencia_delivery  TEXT,
    tempo_casa            TEXT,
    respostas             JSONB        NOT NULL,
    pilares               JSONB        NOT NULL,
    total                 SMALLINT     NOT NULL,
    nivel                 TEXT         NOT NULL,
    score_geral           SMALLINT,
    nivel_por_score       TEXT,
    pilar_fraco           TEXT,
    trilha                TEXT
);
CREATE INDEX IF NOT EXISTS idx_{DB_TABELA}_criado_em ON {TABELA} (criado_em DESC);

-- colunas novas em bases criadas antes da regra do pilar mais fraco
ALTER TABLE {TABELA} ADD COLUMN IF NOT EXISTS score_geral     SMALLINT;
ALTER TABLE {TABELA} ADD COLUMN IF NOT EXISTS nivel_por_score TEXT;
ALTER TABLE {TABELA} ADD COLUMN IF NOT EXISTS pilar_fraco     TEXT;
ALTER TABLE {TABELA} ADD COLUMN IF NOT EXISTS trilha          TEXT;
"""


def conectar():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não definida (crie o arquivo .env).")
    return psycopg2.connect(url, connect_timeout=10)


def init_db():
    """Cria schema e tabela se ainda nao existirem. Seguro em todo boot."""
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA)


# --------------------------------------------------------------------------- #
# Pontuacao
# --------------------------------------------------------------------------- #

def indice_nivel(score):
    """Indice do nivel (0=V0 .. 3=V3) a partir de um score de 0 a 100."""
    indice = 0
    for i, (_, _, minimo) in enumerate(NIVEIS):
        if score >= minimo:
            indice = i
    return indice


def pilar_mais_fraco(scores):
    """Pilar de menor score. No empate vale a ordem Lucrativo > Escolhido >
    Desejado > Visto: sem margem o resto nao se sustenta."""
    return min(scores, key=lambda k: (scores[k], ORDEM_DESEMPATE.index(k)))


def calcular_nivel(score_geral, scores):
    """Nivel final: no maximo um degrau acima do nivel do pilar mais fraco.

    Os scores chegam sem arredondar de proposito — o nivel e calculado antes
    do arredondamento, conforme a regra do diagnostico.
    """
    i_score = indice_nivel(score_geral)
    fraco = pilar_mais_fraco(scores)
    i_fraco = indice_nivel(scores[fraco])
    i_final = min(i_score, i_fraco + 1)
    return {
        "nivel": CODIGOS_NIVEL[i_final],
        "nivel_nome": NOMES_NIVEL[CODIGOS_NIVEL[i_final]],
        "nivel_por_score": CODIGOS_NIVEL[i_score],
        "pilar_fraco": fraco,
        "pilar_fraco_nome": PILARES_NOMES[fraco],
        "nivel_pilar_fraco": CODIGOS_NIVEL[i_fraco],
        "travado": i_final < i_score,
    }


def pontuar(respostas):
    """respostas = {id: rotulo} -> (detalhe_por_pilar, total, score_geral, perfil)."""
    perfil = {}
    for p in PERFIL:
        escolha = respostas.get(p["id"])
        if escolha not in p["opcoes"]:
            raise ValueError(f"Faltou responder: “{p['pergunta']}”")
        perfil[p["campo"]] = escolha

    por_pilar = {chave: [] for chave, _ in PILARES}
    for pergunta in PERGUNTAS:
        escolha = respostas.get(pergunta["id"])
        if escolha not in pergunta["opcoes"]:
            raise ValueError(f"Faltou responder: “{pergunta['pergunta']}”")
        # a posicao da opcao e a propria nota (A=0, B=1, C=2, D=3)
        por_pilar[pergunta["pilar"]].append(pergunta["opcoes"].index(escolha))

    detalhe = {}
    for chave, notas in por_pilar.items():
        pontos = sum(notas)
        detalhe[chave] = {
            "pontos": pontos,                        # 0 a 15
            "score": pontos / PONTOS_PILAR * 100,    # 0 a 100, sem arredondar
        }
    total = sum(d["pontos"] for d in detalhe.values())
    score_geral = total / TOTAL_MAXIMO * 100
    return detalhe, total, score_geral, perfil


def plano_para(nivel, pilar_fraco):
    """Plano de 90 dias do nivel, com o pilar mais fraco no topo."""
    plano = PLANOS[nivel]
    ordem = [pilar_fraco] + [c for c, _ in PILARES if c != pilar_fraco]
    return {
        "nivel": nivel,
        "titulo": plano["titulo"],
        "meses": MESES,
        "linhas": [
            {
                "pilar": chave,
                "nome": PILARES_NOMES[chave],
                "destaque": chave == pilar_fraco,
                "acoes": plano["acoes"][chave],
            }
            for chave in ordem
        ],
        "metas": plano["metas"],
    }


def montar_resultado(pilares_salvos, total, score_geral, nivel, nivel_por_score,
                     pilar_fraco, nome=None, restaurante=None):
    """Remonta o payload da tela de resultado a partir de uma linha do banco."""
    score_fraco = float(pilares_salvos[pilar_fraco]["score"])
    return {
        "ok": True,
        "nome": nome,
        "restaurante": restaurante,
        "score_geral": score_geral,
        "total": total,
        "maximo": TOTAL_MAXIMO,
        "nivel": nivel,
        "nivel_nome": NOMES_NIVEL[nivel],
        "mensagem": MENSAGENS[nivel],
        "travado": CODIGOS_NIVEL.index(nivel) < CODIGOS_NIVEL.index(nivel_por_score),
        "nivel_por_score": nivel_por_score,
        "pilar_fraco": PILARES_NOMES[pilar_fraco],
        "nivel_pilar_fraco": CODIGOS_NIVEL[indice_nivel(score_fraco)],
        "meta": META,
        "escala_radar": ESCALA_RADAR,
        "pilares": [
            {
                "id": chave,
                "nome": PILARES_NOMES[chave],
                "pontos": pilares_salvos[chave]["pontos"],
                "score": round(float(pilares_salvos[chave]["score"])),
                "radar": float(pilares_salvos[chave]["score"]) / 20,
            }
            for chave, _ in PILARES
        ],
        "plano": plano_para(nivel, pilar_fraco),
    }


def buscar_resultado(resposta_id):
    """Resultado de uma resposta ja gravada, ou None se a linha nao existe mais
    (por exemplo depois de um 'Zerar')."""
    with conectar() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT pilares, total, score_geral, nivel, nivel_por_score, "
                f"pilar_fraco, nome, restaurante FROM {TABELA} WHERE id = %s",
                (resposta_id,),
            )
            linha = cur.fetchone()
    if not linha or not linha["pilar_fraco"]:
        return None
    return montar_resultado(
        linha["pilares"], linha["total"], linha["score_geral"],
        linha["nivel"], linha["nivel_por_score"], linha["pilar_fraco"],
        linha["nome"], linha["restaurante"],
    )


def trilha_comercial(nivel, faturamento):
    """Sugestao interna para o time (nao aparece para o participante)."""
    if faturamento == "Acima de R$ 1 milhão":
        return "Enterprise"
    return {"V0": "Basic", "V1": "Basic", "V2": "Intermediário", "V3": "Avançado"}[nivel]


# --------------------------------------------------------------------------- #
# Agregacao para o painel
# --------------------------------------------------------------------------- #

def _distribuicao(valores, ordem):
    total = len(valores)
    return [
        {
            "rotulo": rotulo,
            "n": sum(1 for v in valores if v == rotulo),
            "pct": round(sum(1 for v in valores if v == rotulo) * 100 / total) if total else 0,
        }
        for rotulo in ordem
    ]


def agregar():
    with conectar() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT tipo_negocio, faturamento, dependencia_delivery, tempo_casa, "
                f"pilares, total, nivel, score_geral, pilar_fraco FROM {TABELA}"
            )
            linhas = cur.fetchall()

    total_respostas = len(linhas)

    niveis = []
    for codigo, nome, _ in NIVEIS:
        n = sum(1 for l in linhas if l["nivel"] == codigo)
        niveis.append({
            "codigo": codigo,
            "nome": nome,
            "n": n,
            "pct": round(n * 100 / total_respostas) if total_respostas else 0,
        })

    pilares = []
    for chave, nome in PILARES:
        # no radar o pilar vai de 0 a 5 = score / 20
        notas = sorted(
            (float(l["pilares"][chave]["score"]) / 20 for l in linhas), reverse=True
        )
        if notas:
            corte = max(1, round(len(notas) * 0.25))
            sala = round(sum(notas) / len(notas), 1)
            top25 = round(sum(notas[:corte]) / corte, 1)
        else:
            sala = top25 = 0.0
        pilares.append({
            "id": chave, "nome": nome, "sala": sala, "top25": top25,
            "meta": META, "gap": round(META - sala, 1),
        })

    scores = [l["score_geral"] for l in linhas if l["score_geral"] is not None]
    travas = _distribuicao(
        [PILARES_NOMES.get(l["pilar_fraco"]) for l in linhas],
        [nome for _, nome in PILARES],
    )
    return {
        "total": total_respostas,
        "score_medio": round(sum(scores) / len(scores)) if scores else 0,
        "pontuacao_maxima": TOTAL_MAXIMO,
        "escala": ESCALA_RADAR,
        "meta": META,
        "niveis": niveis,
        "pilares": pilares,
        "trava": travas,
        "mais_forte": max(pilares, key=lambda p: p["sala"]) if total_respostas else None,
        "maior_gap": max(pilares, key=lambda p: p["gap"]) if total_respostas else None,
        "tipo_negocio": _distribuicao(
            [l["tipo_negocio"] for l in linhas], PERFIL_POR_ID["p1"]["opcoes"]),
        "faturamento": _distribuicao(
            [l["faturamento"] for l in linhas], PERFIL_POR_ID["p2"]["opcoes"]),
        "dependencia_delivery": _distribuicao(
            [l["dependencia_delivery"] for l in linhas], PERFIL_POR_ID["p3"]["opcoes"]),
        "tempo_casa": _distribuicao(
            [l["tempo_casa"] for l in linhas], PERFIL_POR_ID["p4"]["opcoes"]),
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    }


# --------------------------------------------------------------------------- #
# Rotas
# --------------------------------------------------------------------------- #

def _senha_admin():
    """Sem padrao no codigo: este repositorio e publico, entao uma senha embutida
    aqui nao protegeria nada. Sem SENHA_ADMIN definida, o painel nao abre."""
    return (os.environ.get("SENHA_ADMIN") or "").strip()


# O formulario e aberto: quem tem o link responde. Senha so no painel.
@bp.route("/", methods=["GET"], strict_slashes=False)
def formulario():
    # Quem ja respondeu volta a ver o proprio resultado e o plano de 90 dias.
    # Se a resposta nao existe mais (o painel foi zerado), o formulario reabre
    # em vez de travar a pessoa numa tela sem saida.
    resultado = None
    resposta_id = session.get("diag_resposta_id")
    if resposta_id:
        try:
            resultado = buscar_resultado(resposta_id)
        except Exception:
            resultado = None
        if resultado is None:
            session.pop("diag_resposta_id", None)

    return render_template(
        "diagnostico_form.html",
        perguntas=perguntas_publicas(),
        resultado=resultado,
    )


@bp.route("/novo", methods=["GET"], strict_slashes=False)
def novo():
    """Libera o mesmo aparelho para outra pessoa responder."""
    session.pop("diag_resposta_id", None)
    session.pop("diag_enviado", None)
    return redirect(url_for("diagnostico.formulario"))


@bp.route("/api/responder", methods=["POST"])
def responder():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    restaurante = (dados.get("restaurante") or "").strip()
    whatsapp = (dados.get("whatsapp") or "").strip()
    aceite = bool(dados.get("aceite_contato"))
    respostas = dados.get("respostas") or {}

    if len(nome) < 2 or len(restaurante) < 2:
        return jsonify({"erro": "Informe seu nome e o nome do restaurante."}), 400

    try:
        detalhe, total, score_geral, perfil = pontuar(respostas)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    scores = {k: v["score"] for k, v in detalhe.items()}
    nivel = calcular_nivel(score_geral, scores)
    trilha = trilha_comercial(nivel["nivel"], perfil.get("faturamento"))

    with conectar() as conn, conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {TABELA} "
            "(nome, restaurante, whatsapp, aceite_contato, tipo_negocio, faturamento, "
            " dependencia_delivery, tempo_casa, respostas, pilares, total, nivel, "
            " score_geral, nivel_por_score, pilar_fraco, trilha) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (
                nome, restaurante, whatsapp or None, aceite,
                perfil.get("tipo_negocio"), perfil.get("faturamento"),
                perfil.get("dependencia_delivery"), perfil.get("tempo_casa"),
                json.dumps(respostas, ensure_ascii=False),
                json.dumps(detalhe), total, nivel["nivel"],
                round(score_geral), nivel["nivel_por_score"],
                nivel["pilar_fraco"], trilha,
            ),
        )
        resposta_id = cur.fetchone()[0]

    session["diag_resposta_id"] = resposta_id
    return jsonify(montar_resultado(
        detalhe, total, round(score_geral), nivel["nivel"],
        nivel["nivel_por_score"], nivel["pilar_fraco"], nome, restaurante,
    ))


# ----------------------------- painel / admin ------------------------------ #

@bp.route("/admin", methods=["GET"], strict_slashes=False)
def admin():
    if not session.get("diag_admin"):
        return render_template("diagnostico_login.html", erro=None)
    return render_template("diagnostico_admin.html")


@bp.route("/admin/login", methods=["POST"])
def admin_login():
    esperada = _senha_admin()
    if not esperada:
        return render_template(
            "diagnostico_login.html",
            erro="Painel sem senha configurada. Defina SENHA_ADMIN no ambiente.",
        ), 503

    senha = (request.form.get("senha") or "").strip()
    if senha == esperada:
        session["diag_admin"] = True
        return redirect(url_for("diagnostico.admin"))
    return render_template("diagnostico_login.html", erro="Senha incorreta."), 401


@bp.route("/api/dados", methods=["GET"])
def api_dados():
    if not session.get("diag_admin"):
        return jsonify({"erro": "não autorizado"}), 403
    return jsonify(agregar())


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
        ["Data", "Nome", "Restaurante", "WhatsApp", "Aceitou contato",
         "Tipo de negócio", "Faturamento", "Dependência de delivery", "Tempo de casa"]
        + [f"{nome} (score)" for _, nome in PILARES]
        + ["Total (0-60)", "Score geral", "Nível", "Nível pelo score",
           "Pilar que trava", "Trilha sugerida"]
        + [p["id"] for p in PERGUNTAS]
    )
    for l in linhas:
        escritor.writerow(
            [
                l["criado_em"].strftime("%d/%m/%Y %H:%M"),
                l["nome"], l["restaurante"], l["whatsapp"] or "",
                "sim" if l["aceite_contato"] else "não",
                l["tipo_negocio"], l["faturamento"],
                l["dependencia_delivery"], l["tempo_casa"],
            ]
            + [round(l["pilares"][chave]["score"]) for chave, _ in PILARES]
            + [l["total"], l["score_geral"], l["nivel"], l["nivel_por_score"],
               PILARES_NOMES.get(l["pilar_fraco"], ""), l["trilha"] or ""]
            + [l["respostas"].get(p["id"], "") for p in PERGUNTAS]
        )

    return Response(
        # BOM para o Excel abrir os acentos certo
        "﻿" + buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=diagnostico-cozinha-campea.csv"},
    )


@bp.route("/admin/limpar", methods=["POST"])
def limpar():
    """Zera as respostas (uso antes do evento, para descartar os testes)."""
    if not session.get("diag_admin"):
        return jsonify({"erro": "não autorizado"}), 403
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(f"TRUNCATE {TABELA} RESTART IDENTITY")
    return jsonify({"ok": True})
