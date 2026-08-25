# PROMPT — LANDING PAGE
# RESTAURANTE CAMPEÃO: como aumentar as vendas do seu restaurante
### Encontro presencial · Cozinha Campeã (Clara Senra) × V4 Company (Lisboa & Co) · 29 de setembro · TV Sim, Belo Horizonte

---

## 0. VARIÁVEIS AINDA EM ABERTO

Preencha antes de rodar. **Nenhum token pode aparecer em tela.**

| Token | O que é |
|---|---|
| `{VALOR}` | Valor do ingresso |
| `{LINK_CHECKOUT}` | URL do checkout |
| `{ENDERECO}` | Endereço completo da TV Sim |

Todo o resto da página já está com dado real e verificado. **Regra dura: nenhum número novo pode ser criado, arredondado ou estimado. Use exclusivamente os números escritos neste prompt.**

---

## 1. CONTEXTO E OBJETIVO

Landing page **single-page, alta conversão**, para captação de inscrições.

- **Evento:** RESTAURANTE CAMPEÃO — Como aumentar as vendas do seu restaurante
- **Data:** terça-feira, 29 de setembro de 2026
- **Local:** TV Sim — {ENDERECO} — Belo Horizonte
- **Horário:** 18h às 22h
- **Capacidade:** 120 donos de restaurante. Número fechado.
- **Realização:** Cozinha Campeã, de Clara Senra, em parceria com a V4 Company
- **Objetivo único:** gerar inscrições. Todo elemento existe para levar ao CTA.

**Tese que a página inteira sustenta:** o restaurante que vende mais hoje não é o que cozinha melhor — é o que domina três frentes ao mesmo tempo: **ser visto** (mídia e influência), **ser desejado** (posicionamento e rede social) e **ser lucrativo** (gestão, dados e IA). Clara Senra prova a primeira. A V4 prova a terceira. Juntas, elas são a única dupla em Minas que consegue mostrar as três na mesma noite.

---

## 2. PÚBLICO E TOM

**Público:** donos e sócios de restaurantes, bares, cafés e casas de eventos de BH e região. Opera no dia a dia, conhece a cozinha, sente a margem apertar, desconfia de discurso de agência, tem pouco tempo.

**Tom:** direto, adulto, sem promessa milagrosa. Frases curtas. Verbo forte. Zero jargão de marketing não explicado. A página fala como quem já esteve dentro de um restaurante em noite cheia.

**Proibido:** "revolucionar", "transformar sua vida", "segredo que ninguém conta", "método infalível", "escale seu negócio", emojis, exclamações em série.

---

## 3. STACK E REQUISITOS

- React + TypeScript + Tailwind CSS
- Framer Motion: fade + subida de 16px, `once: true`, 0.5s, easing suave. Sem parallax pesado.
- Lucide React para ícones, traço fino, cor herdada.
- **Mobile-first.** O tráfego virá do Instagram, no celular. Desenhe para 390px e expanda.
- Página única, sem rotas. Navegação por âncora suave.
- Todos os CTAs vão para `{LINK_CHECKOUT}` em nova aba com `rel="noopener noreferrer"`.
- Semântica: `<header>`, `<main>`, `<section>`, `<footer>`, um único `<h1>`.
- Acessibilidade AA, `alt` em todas as imagens, foco visível.
- `loading="lazy"` em tudo, exceto o hero.

---

## 4. DESIGN SYSTEM — FUSÃO COZINHA CAMPEÃ × V4

A **estrutura visual é do Cozinha Campeã** (paleta extraída do material oficial da marca); a **cor de ação e o rigor tipográfico são da V4**.

```css
--creme:          #F7F0E5;  /* fundo das seções claras — é a base da marca, não use branco puro */
--branco-quente:  #FFFDF9;  /* cards sobre creme */
--carvao:         #171719;  /* fundo das seções escuras */
--carvao-card:    #242426;  /* cards sobre fundo escuro */
--vermelho-cc:    #CB161F;  /* vermelho Cozinha Campeã — títulos de destaque, blocos cheios */
--vermelho-v4:    #E30613;  /* cor de AÇÃO — exclusivo de botões e CTAs */
--ambar:          #FF9418;  /* acento Cozinha Campeã — kickers, numeração, dados */
--cinza-texto:    #625E58;  /* apoio sobre creme */
```

**Regras de cor:**
- Âmbar é a cor dos **kickers e dos números**. Vermelho `--vermelho-cc` é a cor dos **destaques de título e blocos cheios**. `--vermelho-v4` é **só botão**. Nunca misture os dois vermelhos no mesmo elemento.
- Alterne fundo creme e fundo carvão a cada seção. Não use duas seções escuras seguidas.
- Sem gradiente colorido, sem glassmorphism, sem sombra colorida.

**Tipografia:** Archivo em toda a página.
- H1: Archivo Black, 40px mobile / 68px desktop, `leading-[0.98]`, `tracking-tight`
- H2: Archivo ExtraBold, 30px / 48px, `leading-[1.05]`
- Kicker: Archivo Bold, 11px / 12px, `uppercase`, `tracking-[0.16em]`, cor `--ambar`
- Corpo: Archivo Regular, 16px / 18px, `leading-relaxed`, máx. 62 caracteres por linha
- Números: Archivo Black, 34px / 52px, com rótulo pequeno em cinza logo abaixo

**Componentes:**
- **Cards:** `--branco-quente` sobre creme, `--carvao-card` sobre escuro. Raio **12px** (o Cozinha Campeã usa cantos generosos — respeite). Sombra sutil e neutra ou nenhuma. Numeração `01 · 02 · 03` em âmbar no topo.
- **Card de destaque:** um card por grupo pode ser preenchido em `--vermelho-cc` ou `--carvao` sólido, com texto invertido. Sempre o último da linha.
- **Botão primário:** `--vermelho-v4`, texto branco, caixa alta, Archivo Bold, altura 56px, raio 8px, hover escurece 8% e sobe 2px.
- **Botão secundário:** transparente, borda 1px, mesmo tamanho.
- **Espaçamento vertical:** 80px mobile / 140px desktop. Respiro é parte da identidade.
- **Lockup de marcas:** logo Cozinha Campeã + "×" fino + logo V4 Company, sempre na mesma linha de base e com alturas ópticas equivalentes.

---

## 5. ESTRUTURA — SEÇÃO A SEÇÃO, COM COPY FINAL

> Copy final. Use exatamente como está. Não reescreva, não "melhore", não adicione seção que não esteja aqui.

### 5.1 · Barra fixa superior
Altura 48px, fundo `--carvao`, fixa.
- Esquerda: lockup COZINHA CAMPEÃ × V4 COMPANY
- Centro: contador regressivo até 29/09/2026 às 18h — `00d 00h 00m 00s`
- Direita: botão `--vermelho-v4` compacto **GARANTIR MINHA VAGA**
- Mobile: esconde o contador, mantém lockup e botão.

### 5.2 · Hero
Fundo: foto real em full-bleed (salão de restaurante cheio à noite ou Clara em ambiente gastronômico). Overlay `--carvao` a 68%, mais denso à esquerda. Conteúdo alinhado à esquerda, altura mínima 92vh.

- **Kicker:** 29 DE SETEMBRO · TV SIM · BELO HORIZONTE · 120 DONOS DE RESTAURANTE
- **H1:** RESTAURANTE CAMPEÃO: **como aumentar as vendas do seu restaurante.** *(segunda linha em `--ambar`)*
- **Subheadline:** Casa cheia não paga conta. Uma noite com Clara Senra e a V4 Company para 120 donos de restaurante que cansaram de depender do boca a boca, da taxa do aplicativo e da sorte de terça-feira. Aqui você vai entender o que separa um restaurante movimentado de um restaurante campeão: ser visto, ser desejado e ser lucrativo.
- **Chips de dados** (ícone fino + texto, separados por borda vertical): `29 de setembro` · `18h às 22h` · `TV Sim · Belo Horizonte` · `Presencial` · `120 vagas`
- **CTA primário:** GARANTIR MINHA VAGA
- **CTA secundário:** VER A PROGRAMAÇÃO *(âncora para 5.6)*
- **Microcopy:** As inscrições encerram quando a 120ª vaga for preenchida. Sem transmissão online e sem gravação.

### 5.3 · Faixa de autoridade
Fundo `--creme`, altura contida.
- Texto pequeno centralizado acima: **MARCAS QUE JÁ CRUZARAM A TRAJETÓRIA DO COZINHA CAMPEÃ**
- Linha horizontal de logos: Itatiaia · Band · Supermercados BH · Drogaria Araújo · Vilma Alimentos · Localiza · Shopping Del Rey · Sesc · Prefeitura de BH
- Tratamento em escala de cinza, opacidade 70%, scroll horizontal discreto no mobile.
- **Só publique logo com autorização de uso formal.** Sem autorização, exiba os nomes em tipografia — nunca a marca.

### 5.4 · Seção-tese *(fundo `--creme`)*
- **Kicker:** A CONVERSA QUE NINGUÉM TEM COM VOCÊ
- **H2:** Comida boa virou o mínimo. **O que faz vender hoje está fora da cozinha.** *(segunda frase em `--vermelho-cc`)*
- **Parágrafo:** Todo dono de restaurante acredita que tem o melhor prato do bairro — e muitos têm mesmo. O problema é que o cliente já não escolhe pelo prato. Ele escolhe pelo que viu no feed, por quem indicou, pela avaliação que leu e pela primeira casa que apareceu quando bateu a fome. Enquanto isso, o CMV sobe, a taxa do aplicativo come a margem e a conta do mês chega igual. Restaurante campeão não é o mais gostoso: é o que domina três frentes ao mesmo tempo.

**Três cards:**

**01 · SER VISTO** — Mídia e influência
Restaurante que não aparece não é lembrado. Quem sabe usar influenciador do segmento, rádio, programa e festival compra uma atenção que nenhum anúncio entrega sozinho — e compra pelo custo que o concorrente da esquina não sabe negociar.

**02 · SER DESEJADO** — Posicionamento e rede social
Seguidor não paga conta; desejo, sim. Perfil bem gerido não é vitrine de foto de prato: é máquina de gerar vontade, justificar preço e transformar audiência em fila na porta numa terça-feira comum.

**03 · SER LUCRATIVO** — Gestão, dados e IA
Movimento sem número é sorte, e sorte acaba. Ticket médio, CMV, recorrência, custo por cliente novo, horário de pico ocioso: quem enxerga esses dados e usa inteligência artificial na rotina decide em minutos o que os outros levam meses para descobrir.

### 5.5 · Prova do pilar "ser visto" *(fundo `--carvao`)*
Seção nova e obrigatória — é o que dá autoridade real à noite.

- **Kicker:** A AUDIÊNCIA QUE DECIDE ONDE SUA CIDADE VAI COMER
- **H2 (branco):** Enquanto você espera o cliente entrar, alguém já está falando com ele.
- **Linha de apoio:** Os números abaixo são do ecossistema Cozinha Campeã. Eles não estão aqui para impressionar — estão aqui para você entender o tamanho da atenção que está disponível no seu segmento e que a maioria dos restaurantes nunca aprendeu a usar.

**Bloco de números** — número em `--ambar`, rótulo em cinza claro. Grid 2 colunas no mobile, 5 no desktop:
- `13,8 milhões` — visualizações no Instagram em 90 dias
- `5,7 milhões` — contas alcançadas
- `809.522` — interações
- `+270,9 mil` — seguidores e inscritos no ecossistema
- `+3,7 milhões` — impactos mensais estimados do programa Cozinha Campeã

**Sub-bloco de perfil de audiência**, em faixa separada por linha fina, com o título pequeno **QUEM É ESSA AUDIÊNCIA:**
`76,6% mulheres` · `62,3% entre 25 e 44 anos` · `97,2% no Brasil` · `Pico de audiência: 18h às 21h`

- **Frase de fechamento da seção, destacada em `--ambar`:** É exatamente o público que decide onde a família vai jantar — e no exato horário em que essa decisão é tomada.

**Faixa complementar**, texto menor, sobre a distribuição: O programa Cozinha Campeã vai ao ar às sextas, 20h, no YouTube do Itatiaia Esporte — dentro de uma operação que soma 5,1 milhões de ouvintes em 30 dias, 95% de cobertura de Minas Gerais, 624 cidades e 85 emissoras afiliadas.

### 5.6 · Programação *(fundo `--vermelho-cc`, texto branco)*
- **Kicker (branco):** A PROGRAMAÇÃO DA NOITE
- **H2 (branco):** Quatro horas para transformar reputação em movimento — e movimento em margem.
- **Linha de apoio:** Não é palestra motivacional. É diagnóstico, método e plano. Você entra com um restaurante e sai com uma lista do que fazer nos próximos 90 dias.

**Timeline vertical, 8 blocos** (linha fina branca, marcadores numerados, horário em destaque):

| # | Horário | Título | Descrição |
|---|---|---|---|
| 01 | 18:00 | Credenciamento e networking | Chegue cedo. A sala tem 120 donos de restaurante de Belo Horizonte — parte do valor da noite acontece antes do palco. |
| 02 | 18:40 | Abertura: casa cheia não paga conta — *Clara Senra* | A anfitriã abre a noite com o que aprendeu circulando por centenas de cozinhas, programas e festivais: por que alguns restaurantes viram destino e outros viram só mais uma opção no aplicativo. |
| 03 | 19:20 | O restaurante que aparece | Como funciona, na prática, a mecânica de mídia e influência no segmento de alimentação: o que gera fila, o que gera só curtida e o que é dinheiro jogado fora. |
| 04 | 20:00 | Pausa e networking | Vinte minutos para tomar um café e trocar com quem vive o mesmo problema que você. |
| 05 | 20:20 | Gestão de alta performance — *Gabriel Soares, V4 Company* | Os números que todo dono de restaurante deveria olhar toda segunda-feira, onde está o gargalo real do seu faturamento e como a inteligência artificial encurta a distância entre o dado e a decisão. |
| 06 | 21:00 | Mapa de oportunidades ao vivo | Casos reais de restaurantes destrinchados na frente da sala. Você vai reconhecer o seu em pelo menos um deles. |
| 07 | 21:30 | Plano de 90 dias | Cada participante sai com um plano de ação escrito: o que atacar primeiro, o que pode esperar e o que precisa parar de fazer imediatamente. |
| 08 | 22:00 | Encerramento | Conversa aberta com Clara, com o time da V4 e com os outros donos da sala. |

### 5.7 · Clara Senra *(fundo `--creme`, foto à esquerda, texto à direita)*
- **Kicker:** A ANFITRIÃ DA NOITE
- **H2:** Clara Senra
- **Função:** Jornalista gastronômica · Apresentadora do Cozinha Campeã · Criadora do ecossistema Cozinha Campeã
- **Bio:** Mineira de Belo Horizonte, Clara é jornalista gastronômica desde 2011 e construiu o que quase nenhum restaurante consegue construir sozinho: autoridade e audiência ao mesmo tempo. Passou pelo MasterChef Brasil em 2015, pela PUC TV, pelo Canal Futura e pela Band Minas, e desde 2023 está na Itatiaia, onde assina a editoria de gastronomia e apresenta o Cozinha Campeã. Hoje transforma repertório editorial em produtos, experiências e negócios — e conhece por dentro a diferença entre o restaurante que aparece e o restaurante que fatura.
- **Frase de destaque em `--vermelho-cc`, tamanho maior:** Carisma para aproximar. Credibilidade para recomendar. Consistência para converter.
- **Linha do tempo horizontal** (marcadores em creme sobre linha fina, último ponto em âmbar): `2011` jornalismo gastronômico · `2015` MasterChef Brasil · `2016` PUC Minas · `2020` Band Minas · `2023` Itatiaia · `2025` programa solo · `2026` ecossistema em expansão

### 5.8 · Gabriel Soares / V4 Company *(fundo `--carvao`)*
- **Kicker:** O CONVIDADO
- **H2 (branco):** Gabriel Soares
- **Função:** Diretor e sócio · V4 Company
- **Bio:** A V4 Company é a maior operação de assessoria de marketing e vendas do Brasil, com metodologia própria de crescimento aplicada a milhares de negócios. À frente da unidade de Minas Gerais, Gabriel conduz operações de gestão comercial, tráfego, dados e inteligência artificial — e o setor de alimentação é um dos que mais passam pela sua mesa. Na noite do 29, ele traz o lado que quase nunca entra na conversa de restaurante: o número.
- **Bloco de números** (âmbar): `+6 anos` de operação · `+500` restaurantes atendidos

### 5.9 · Para quem é / Para quem não é *(fundo `--creme`, duas colunas)*
- **H2:** Essa noite não é para todo mundo.

**É PARA VOCÊ SE:** *(checks em `--vermelho-cc`)*
- Você é dono ou sócio de restaurante, bar, café ou casa de eventos
- Sua casa até enche, mas o dinheiro não sobra no fim do mês
- Você depende do aplicativo de delivery mais do que gostaria
- Você posta nas redes, mas não sabe dizer quanto isso trouxe de volta
- Você já pensou em trabalhar com influenciador e não sabe como fazer isso dar retorno

**NÃO É PARA VOCÊ SE:** *(traços em cinza)*
- Você quer uma fórmula pronta que funcione sem mudar nada na operação
- Você acha que comida boa se vende sozinha
- Você não está disposto a olhar os números do próprio negócio

### 5.10 · Prova social *(fundo `--carvao`)*
- **Kicker:** QUEM JÁ ESTEVE NA SALA
- **H2 (branco):** Empresários que participaram, aplicaram e sentiram a diferença.
- Três cards verticais 9:16, thumbnail de vídeo, play central em `--vermelho-v4`, legenda com nome e negócio.
- **Regra:** apenas depoimentos reais fornecidos. Se houver menos de três, centralize os que existirem. **Nunca gere depoimento, nome ou foto fictícia.** Se não houver nenhum, remova a seção inteira.

### 5.11 · Oferta *(fundo `--vermelho-cc`, seção-âncora do CTA)*
- **H2 (branco, centralizado):** Garanta sua vaga presencial.
- **Preço:** `R$` pequeno + `{VALOR}` em Archivo Black gigante
- **Linha de apoio:** por pessoa · inscrição individual
- **Incluído** (checks brancos):
  - Acesso à noite completa, das 18h às 22h, na TV Sim
  - Plano de 90 dias para o seu restaurante, construído durante o evento
  - Networking direto com 120 donos de restaurante de Belo Horizonte
  - Encontro com Clara Senra e com o time da V4 Company
- **CTA:** QUERO MINHA VAGA
- **Microcopy:** 120 vagas. Sem transmissão online. Sem segunda turma em 2026.

### 5.12 · FAQ *(fundo `--creme`, acordeão, um item aberto por vez)*
1. **Para quem é esse evento?** Para donos e sócios de restaurantes, bares, cafés e casas de eventos. Se você não decide sobre o negócio, o conteúdo vai render menos para você.
2. **Preciso entender de marketing?** Não. A noite foi desenhada para quem opera restaurante, não para quem trabalha com marketing. Nada será explicado em código.
3. **Vou sair com alguma coisa na mão?** Sim. O plano de 90 dias é construído durante o evento, com o seu restaurante como base.
4. **Vai ter transmissão ou gravação?** Não. O encontro é presencial e não será transmitido nem disponibilizado depois.
5. **Posso levar meu sócio ou meu gerente?** Pode, e recomendamos — mas cada pessoa ocupa uma vaga e precisa de inscrição própria.
6. **Como confirmo minha inscrição?** Após a compra você recebe um e-mail de confirmação com endereço, horário e orientações de acesso à TV Sim.

### 5.13 · CTA final e rodapé
- Faixa `--carvao` com H2 em branco: **29 de setembro. 18h. TV Sim. 120 vagas.** e botão `--vermelho-v4` GARANTIR MINHA VAGA.
- Rodapé: lockup COZINHA CAMPEÃ × V4 COMPANY, links para o Instagram das duas marcas e a linha "Realização: Cozinha Campeã e V4 Company."

---

## 6. COMPORTAMENTOS

- Contador regressivo funcional para 29/09/2026 18h, atualizando a cada segundo, com fallback "As inscrições foram encerradas" ao zerar.
- Botão flutuante de CTA no mobile, fixo no rodapé, aparecendo depois que o usuário passa do hero.
- Scroll suave nas âncoras. Hover em todo elemento clicável.

---

## 7. NÃO FAÇA — LISTA EXPLÍCITA

1. **Não descreva, liste, detalhe ou precifique nenhum serviço, produto ou entregável da parceria comercial** — nada de tráfego pago, gestão de rede social, dashboard, publicações, backbus, cotas, permuta ou pacote. A página vende a experiência da noite, não a oferta comercial. Regra dura.
2. **Não crie nenhum número.** Use apenas os desta especificação. Sem percentual de crescimento, sem "média de mercado", sem estatística de setor, sem case inventado.
3. Não invente depoimento, nome, foto de cliente ou print de resultado.
4. Não altere, reescreva ou "melhore" a copy da seção 5.
5. Não adicione seção fora da lista — sem blog, sem newsletter, sem contador de "alunos", sem chatbot, sem selo de garantia.
6. Não crie múltiplas páginas ou rotas.
7. Não use lorem ipsum em nenhuma hipótese.
8. Não use gradiente multicolorido, glassmorphism, neon, sombra colorida, ícone 3D ou emoji.
9. Não use fonte fora de Archivo.
10. Não use branco puro (#FFFFFF) como fundo de seção — a base clara é `--creme`.
11. Não misture `--vermelho-cc` e `--vermelho-v4` no mesmo elemento, e não use `--vermelho-v4` fora de botão.
12. Não coloque carrossel automático, vídeo com autoplay com som ou pop-up de saída.
13. Não crie formulário longo. Se houver formulário: nome, WhatsApp, e-mail e nome do restaurante. Nada além disso.
14. Não use foto de banco de imagem com cara de stock americano. As imagens devem ser do universo Cozinha Campeã ou de restaurantes brasileiros reais.
15. Não use dark mode toggle.
16. Não empilhe mais de dois CTAs visuais distintos por seção.
17. Não use as palavras "workshop", "masterclass", "imersão" ou "mentoria". O evento é um **encontro**.
18. Não exiba a marca Indikey isolada nem em destaque — o lockup é Cozinha Campeã × V4 Company.

---

## 8. CRITÉRIO DE ACEITE

- Abre em menos de 2s no mobile, sem layout shift no hero.
- Nenhum token `{...}` visível em tela.
- Toda a copy da seção 5 presente, na ordem, sem alteração.
- Nenhum serviço ou preço de serviço da parceria em nenhum ponto da página.
- Todos os números da página conferem com esta especificação, um a um.
- Todos os CTAs levam a `{LINK_CHECKOUT}`.
- Leitura confortável em 390px, sem corte de texto e sem scroll horizontal.
- Contraste do texto sobre a imagem do hero passa em AA.
