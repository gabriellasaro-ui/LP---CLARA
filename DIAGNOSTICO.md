# Diagnóstico de Maturidade Comercial

Formulário do evento + painel ao vivo. Roda dentro da mesma app Flask da LP.

## Endereços

| Tela | URL | Senha |
|---|---|---|
| Formulário (participantes) | `/diagnostico` | **aberto**, sem senha |
| Painel de resultados | `/diagnostico/admin` | definida em `SENHA_ADMIN` |
| Captura de planos | `/planos` | **aberta**, sem senha |

O formulário é aberto: quem tem o link responde. A senha do painel vem só da variável
de ambiente `SENHA_ADMIN` — **este repositório é público, então nenhuma senha real
aparece aqui nem no código**. Sem `SENHA_ADMIN` definida, o painel não abre.

`/diagnostico/novo` libera o mesmo aparelho para outra pessoa responder. Não há botão
para isso na tela — é uma URL manual, para o caso de alguém emprestar o celular.

## Como funciona

1. O participante abre o link (sem senha).
2. Responde **4 perguntas de perfil** (tipo de negócio, faturamento, dependência de
   delivery, tempo de casa) — não pontuam, alimentam os recortes do painel.
3. Responde as **20 perguntas pontuadas**, 5 em cada pilar. Cada uma vale de 0 a 3
   (A=0, B=1, C=2, D=3); a pontuação não aparece na tela.
4. No fim informa **nome, restaurante e WhatsApp**, com aceite explícito de LGPD.
   O resultado aparece mesmo para quem não aceita o contato.
5. Vê o próprio resultado com o plano de 90 dias.
6. O painel lê as agregações e se atualiza sozinho a cada 10 segundos.

**Pilares:** Ser visto · Ser desejado · Ser escolhido · Ser lucrativo.

### Score

- **Score do pilar** = pontos do pilar (0–15) ÷ 15 × 100 → 0 a 100
- **Score geral** = pontos totais (0–60) ÷ 60 × 100 → 0 a 100
- No **radar** cada pilar aparece de 0 a 5 (score ÷ 20). A **meta é 4**, ou seja 80 pontos.

### Nível

1. Pelo score geral: **V0** < 40 · **V1** 40–59 · **V2** 60–79 · **V3** 80–100.
2. **Regra do pilar mais fraco:** o nível final fica, no máximo, **um degrau acima** do
   nível do pilar mais fraco. A decisão vem da frente mais fraca.
3. **Empate** no pilar mais fraco: vale a ordem Lucrativo → Escolhido → Desejado → Visto.
4. **Arredondamento:** os scores são exibidos inteiros, mas o nível é calculado antes
   de arredondar.

Nomes: V0 Improviso · V1 Fundação · V2 Gestão · V3 Restaurante Campeão.

Os três exemplos do artefato (Restaurantes A, B e C) estão cobertos por teste — inclusive
o caso do A, que cai de V2 para V1 travado pelo pilar Lucrativo.

### Resultado individual

A tela mostra, nesta ordem: score geral grande, nível com o nome, mensagem do nível,
radar dos quatro pilares, o pilar que mais trava e o **plano de 90 dias do nível**, com
a linha do pilar mais fraco no topo e destacada. Fecha com as metas para o nível seguinte.

Os textos dos planos ficam em `PLANOS`, no `diagnostico.py`.

### Trilha comercial (interna)

Calculada e gravada junto, mas **não aparece no painel nem para o participante** — sai só
no CSV: V0/V1 → Basic · V2 → Intermediário · V3 → Avançado. Faturamento acima de
R$ 1 milhão vai direto para Enterprise.

> O critério "mais de uma unidade" do artefato não é perguntado no formulário, então a
> regra do Enterprise usa só o faturamento.

## Página de planos (`/planos`)

Uma seção só, em duas etapas: **1 · Seus dados** (nome, restaurante, e-mail e telefone)
e **2 · Escolha o plano** (Basic, Intermediário, Avançado e Enterprise como cartões
selecionáveis). Fecha com o botão **Registrar interesse** e uma tela de agradecimento.

A **escassez é mensagem, não trava**: o texto de `ESCASSEZ` aparece na página, mas nada
é contado nem bloqueado. Ninguém fica de fora por causa de um contador, e a página nunca
revela quantas pessoas já se inscreveram — o que seria o oposto de escassez com poucos
cadastros.

Grava em tabela própria — `dashboard_tvsim.interesse_planos` — separada do diagnóstico.
Preços, valores e itens de cada plano ficam em `OFERTA`, no `planos.py`.

No painel de admin há uma aba **Interessados** com:

- quantos registraram interesse e o **potencial mensal na mesa** (soma dos planos
  escolhidos; Enterprise fica fora da conta por ser sob medida);
- filtro por plano;
- lista com nome, restaurante, plano e valor, e-mail e telefone clicáveis, selo **novo**
  para quem chegou na última hora e **botão de WhatsApp** por pessoa;
- export CSV.

Ela usa a mesma sessão de admin do diagnóstico.

## Onde os dados ficam

Tabela **dedicada só a este formulário**: `dashboard_tvsim.diagnostico_cozinha`.

Ela é separada de `dashboard_tvsim.respostas_comercial` (o questionário anterior, com
15 perguntas p1–p15 e 3 pilares). Os dois não se misturam e nenhuma rotina daqui
lê ou escreve na tabela antiga.

Além das notas, a tabela guarda o contato (`nome`, `restaurante`, `whatsapp`) e o
`aceite_contato` — use esse campo para filtrar quem pode ser abordado depois.

## Variáveis de ambiente

Local: copie `.env.example` para `.env` e preencha. O `.env` está no `.gitignore` e no
`.dockerignore`, então **não** vai para o git nem para a imagem Docker.

No EasyPanel, cadastre as mesmas chaves na aba de Environment do serviço:

```
DATABASE_URL=postgresql://USUARIO:SENHA@HOST_INTERNO:5432/NOME_DO_BANCO?sslmode=disable
SENHA_ADMIN=...
SECRET_KEY=...
DIAG_SCHEMA=dashboard_tvsim
DIAG_TABELA=diagnostico_cozinha
```

> Rodando **dentro** do EasyPanel use a URL de conexão **interna** (porta 5432);
> a **externa** só é necessária quando a app roda fora, como na Vercel ou na máquina
> local. As duas URLs estão nas credenciais do serviço Postgres, no painel do EasyPanel.

A tabela é criada sozinha no primeiro boot (`CREATE TABLE IF NOT EXISTS`).
Se o banco estiver fora do ar, a LP continua servindo normalmente — só o diagnóstico para.

## No dia do evento

- **Baixar CSV** exporta todas as respostas com contato, aceite de LGPD, scores por
  pilar, nível e trilha sugerida (separador `;`, abre direto no Excel).
- O painel é feito para projeção: abra em tela cheia e deixe rodando.

### Descartar as respostas de teste

O painel **não tem botão de apagar** — num telão ao vivo, um clique errado custaria
todas as respostas da sala. A rota existe, mas só responde a um POST deliberado,
já autenticado como admin:

```bash
curl -X POST https://SEU-DOMINIO/diagnostico/admin/limpar \
  -H "Cookie: session=<cookie de uma sessão de admin>"
```

Na prática, o mais simples é limpar direto no banco antes do evento:

```sql
TRUNCATE dashboard_tvsim.diagnostico_cozinha RESTART IDENTITY;
```

## Rodando local

```bash
pip install -r requirements.txt
python app.py
# http://127.0.0.1:5016/diagnostico
```
