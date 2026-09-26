# Farmácia — tudo o que foi definido até aqui (Classificador de Backlog)

Agente de **Farmácia** do Classificador de Backlog, com **link próprio** (separado do classificador geral):
**https://claude.ai/artifact/FBP4i6ZktAFc1ymeYWmyP7** (arquivo `classificador/farmacia.html`, gerado pelo `build.py`).
O classificador geral continua em https://claude.ai/artifact/UFuhJCnyT5Lwi3wYZVMVu1 (sem as mudanças de Farmácia).
Código-fonte: repositório `marcato-app/felipefreitas`, pasta `classificador/`, branch `claude/wonderful-babbage-6qodc6`.

---

## 1. Texto para colar como instrução do agente de Farmácia

> Você é o agente de **Farmácia** do Classificador de Backlog (SKUs de varejo, padrão Scanntech). Para cada item de
> Farmácia você decide **categoria, marca, fabricante, conteúdo e descritivo padronizado**, seguindo as regras abaixo.
>
> 1. **Categoria** — é a EST MER 7 da árvore Scanntech (às vezes a própria EST MER 6), **sempre com o código ATC no
>    nome oficial** (ex.: `A02B1 ANTAGONISTAS H2`, `N02B NAO NARCOTICOS ANTIPIRETICOS`). Use a lista
>    `dados/farma_categorias.xlsx`. Quando a descrição tem um **princípio ativo** da base
>    (`dados/farma_principios_ativos.csv`), a categoria é a do princípio ativo. Combinações e formas exigem **todos**
>    os termos (AMOXICILINA + CLAVULANATO; TIMOLOL + COLÍRIO; CETOCONAZOL + CREME → tópico, CETOCONAZOL comprimido →
>    sistêmico); a regra mais específica ganha; empate: o princípio que aparece primeiro. Produto veterinário (CÃO,
>    GATO, PET, VET) **não** vai para Farmácia humana. Produto de outra cesta que só contém o princípio (shampoo com
>    cetoconazol, bicarbonato culinário) fica na sua cesta.
> 2. **Fabricante = sempre o laboratório escrito na descrição**, conferido com o dicionário de fabricantes
>    (grafia oficial do dicionário). Reconhecer por nome completo (EMS, EUROFARMA, MEDLEY, PRATI DONADUZZI…), por
>    código de 3 letras **no fim da descrição** (EMS, EUR, NEO, TEU, CIM, GER, PRD…) e por apelidos de laboratório que a
>    base registra pelo grupo (GERMED/LEGRAND → EMS PHARMA; NEO QUIMICA → HYPERA PHARMA). Tabela em
>    `dados/farma_laboratorios.xlsx`. Nunca usar só a 1ª palavra do nome do fabricante. Sem laboratório na descrição:
>    fica o fabricante do arquivo; sem ele, o da marca.
> 3. **Marca** — remédio de marca: o **nome comercial** (DORFLEX, NEOSALDINA). Genérico (nome do princípio ativo /
>    substância): a **marca é o próprio princípio ativo** e o **fabricante é o laboratório**
>    (`LOSARTANA POTASSICA 50MG 30 COMP GERMED` → marca LOSARTANA, fabricante EMS PHARMA). Laboratório (EMS, CIM,
>    MEDLEY…), GENERICO e sal (CLOR, MAG, BROMETO…) nunca são marca. **Ordem das bases: DIMA primeiro**, depois a base
>    de marcas de Farmácia do cliente (`dados/farma_marcas/`), depois o dicionário enviado; só então o nome comercial
>    escrito na descrição ou o princípio ativo.
> 4. **Descritivo** — marca + complemento + **dosagem** + quantidade na forma farmacêutica:
>    `DIPIRONA SODICA 500MG 10CPRS`, `OMEPRAZOL 20MG 28CAPS`, `NEOSALDINA 30DRGS`, `TIMOLOL COLIRIO 0.5% 5ML`.
>    Comprimidos = CPRS, cápsulas = CAPS, drágeas = DRGS (a palavra COMPRIMIDO/CAPSULA/DRAGEA sai). O laboratório não
>    entra no descritivo. Categorias com abreviação fixa no manual (ex.: `SUPL ALIM`, `CURATIVO`) começam por ela.
>    Outras formas por extenso: SUSP = SUSPENSAO, XPE = XAROPE, GTS = GOTAS, POM = POMADA… (nunca "COMPOSTO").
> 5. **Conteúdo** (coluna) — sempre com unidade. Formas farmacêuticas contam como unidade (`30 COMP` → 30UN, `C/10 CPR`
>    → 10UN); líquidos/cremes em ML/G (`COLIRIO 5ML`, `CREME 30G`). Sem nada: 1UN.
> 6. **Prioridade do arquivo** — categoria, marca, fabricante e conteúdo que vierem no arquivo valem; só trocar o que
>    estiver bem fora do comum, **sempre com alerta** (ex.: fabricante do arquivo diferente do laboratório escrito na
>    descrição → vale o laboratório). O descritivo é sempre padronizado.
> 7. A regra "marca só vale se existir na EST MER 6 do item" (usada nas outras cestas) **não** se aplica à Farmácia.
> 8. Laboratórios do grupo saem pelo grupo (GERMED/LEGRAND → EMS PHARMA; NEO QUIMICA → HYPERA PHARMA).
>    CORTICOIDES = `S01B CORTICOIDES`. Pendente: nomes oficiais que faltam.

---

## 2. Arquivos deste pacote

| Arquivo | O que é |
|---|---|
| `dados/dicionario_nomenclaturas_farmaceuticas.xlsx` | Base enviada pelo cliente: Área > Classe > Subclasse > **Princípio Ativo** > Est Mer 6 / Est Mer 7 / código / fonte ("Texto" = confirmado; "Revisão manual - VALIDAR") |
| `dados/farma_principios_ativos.csv` | A base convertida em regras: 622 princípios → 160 categorias. Termos, categoria, nome oficial, se a base pede validação, se o destino foi corrigido, outras categorias possíveis |
| `dados/farma_categorias.xlsx` | As 400 categorias de Farmácia da biblioteca: nome interno, **nome oficial com código**, início do descritivo, EST MER 6 ligada, incluir/excluir, regra do manual |
| `dados/farma_laboratorios.xlsx` | Laboratórios: 201 **códigos de 3 letras** → fabricante (aprendidos da DIMA), **apelidos** (GERMED, NEO QUIMICA…) e os 698 fabricantes de Farmácia da DIMA |
| `dados/dima_farmacia.csv` | Recorte de Farmácia da base DIMA: 9.558 linhas EST MER 6 (ATC) × marca × fabricante |
| `scripts/farma_pa.py` | Converte o dicionário de princípios ativos nas regras (`farmaPA`), com as escolhas e correções abaixo |
| `scripts/nomes_oficiais.py` | Recupera o nome oficial (com código) das categorias |
| `codigo/farmacia_trechos.js` | Os trechos de código de Farmácia do app (princípio ativo, laboratório, descritivo, unidades) |
| `testes/*.csv` + `testes/resultados_esperados.txt` | Casos de teste e o resultado atual do app |

---

## 3. Regras implementadas (detalhe)

### 3.1 Categoria pelo princípio ativo
- Cada princípio vira uma regra com **partes** que precisam aparecer todas: combinações (`AMOXICILINA+CLAVULANATO`,
  `LOSARTANA/…`), forma no nome (`… COLÍRIO` exige COLIRIO|COL|OFT…; `… TÓPICO` exige CREME|POMADA|GEL|LOCAO|SPRAY…) e
  sinônimos entre parênteses (PARACETAMOL|ACETAMINOFENO, AAS, ALBUTEROL, MACROGOL, COLECALCIFEROL, FITOMENADIONA…).
- Só entram regras cuja categoria está ativa.
- O princípio ativo decide quando as regras normais deram Farmácia, nada, ou PET **sem** palavra de animal;
  categoria de outra cesta que bateu pelas regras continua valendo.
- Alerta "Categoria pelo princípio ativo X"; vai para revisão só se a base marca **VALIDAR** (455 das 667 linhas) ou se
  o destino foi **corrigido**.

**Princípio em mais de uma classe na base** (29 casos) — escolha pelo uso no varejo (`PRIMARIA` em `farma_pa.py`):
METOTREXATO → Antimetabólitos; SULFASSALAZINA → Aminosalicilatos intestinais; ADAPALENO → Antiacne tópicos;
ADALIMUMABE/INFLIXIMABE → Anti-TNF; FINASTERIDA/DUTASTERIDA → Inibidores 5-alfarredutase; ESPIRONOLACTONA → Poupadores
de potássio; ÁCIDO FÓLICO → Antianêmicos; CODEÍNA → Analgésicos narcóticos; HIDRÓXIDO DE MAGNÉSIO → Laxantes osmóticos;
HIDROCORTISONA → Corticoides tópicos; DIGOXINA → Glicosídeos cardíacos; LIRAGLUTIDA/SEMAGLUTIDA → Agonistas GLP-1;
ESTREPTOMICINA → Aminoglicosídeos. Os demais ficam com a 1ª linha da planilha.

**Erros evidentes da base corrigidos** (`CORRECOES` em `farma_pa.py`; revisar com o cliente):
Vitamina A → VITAMINA A PURA; Vitamina D → VITAMINA D PURA; Vitamina K → VITAMINA K; Vitamina E → VITAMINA OUTRO
(a base mandava as quatro para VITAMINA B1); Cetorolaco colírio → Anti-inflamatórios oftalmológicos não esteroides
(base: corticoides); Lopinavir/Ritonavir → Outros antivirais (base: antineoplásicos); Lisdexanfetamina →
Psicoestimulantes (base: estimulantes do apetite); Lidocaína → Anestésicos locais tópicos (base: antiarrítmicos);
anti-inflamatórios "Por Defecto" (ibuprofeno, diclofenaco…) → ANTI REUMATICOS NAO ESTEROIDAIS PUROS; antiglaucoma
"S01E2 TOPICOS" → TOPICOS OFTALMOLOGICOS ANTIGLAUCOMA.

### 3.2 Nome oficial das categorias
- Uma limpeza antiga tirou o código ATC do nome de ~380 categorias. O nome interno ficou; o **oficial** (com código)
  é o que sai na planilha e é reconhecido na coluna CATEGORIA do arquivo (com ou sem código).
- Recuperados **238 de 400**. Faltam 162 (umas 20 não têm código mesmo: CURATIVO, SORO FISIOLOGICO…).
- **CORTICOIDES** = `S01B CORTICOIDES` (oftalmológico), decidido com o cliente (`FIXOS` em `nomes_oficiais.py`).

### 3.3 Descritivo
- Categoria sem início fixo no manual (379 de 400): **marca** na frente; sem marca, **princípio ativo** (como está
  escrito na descrição); sem nenhum, o nome do produto.
- Categorias com início fixo mantêm (SUPL ALIM, SUPL ALIM POLIV, SUPL ALIM MULT, CURATIVO, LUVA DE PROCEDIMENTO,
  SORO FISIOLOGICO, AGUA OXIGENADA…).
- Abreviações de forma: COMP/COMPR/CP/CPR/CPS = COMPRIMIDO; CAP/CAPS = CAPSULA; DRG = DRAGEA; SOL = SOLUCAO; SUSP =
  SUSPENSAO; XPE/XAR = XAROPE; GTS = GOTAS; POM = POMADA; AMP = AMPOLA; INJ = INJETAVEL; EFERV = EFERVESCENTE;
  REV = REVESTIDO.
- Dosagem entra no descritivo, depois do complemento (500MG, 0.5%, 2000UI, 250MG/5ML, 875MG+125MG).
- Quantidade na forma: 10CPRS / 28CAPS / 30DRGS (a palavra da forma sai). Laboratório (nome ou código) sai do
  descritivo. Forma colada no número (20CP, 14CPR) é reconhecida.

### 3.4 Conteúdo
- COMP, COMPR, COMPRIMIDO(S), CP, CPR, CPS, CAP, CAPS, CAPSULA(S), DRG, DRAGEA(S) contam como UN.
- Sempre sai unidade (1UN quando não há nada).

### 3.5 Fabricante = laboratório
- Índice de laboratórios montado do dicionário anexado (primeiro) e da DIMA, só em categorias ATC:
  nome completo do fabricante sem LTDA/SA/FARMA/PHARMA/LABORATORIO…; códigos de 3 letras aprendidos do fim das marcas
  de Farmácia (≥ 3 ocorrências e ≥ 80% do mesmo fabricante; ex.: "DOMPERIDONA RAN" → RANBAXY); apelidos fixos
  (GERMED→GER, LEGRAND→LEG, NEO QUIMICA→NEO, NOVA QUIMICA→NVQ, PRATI/PRATI DONADUZZI→PRD, SANOFI→SNF, MULTILAB→MUL,
  MANTECORP→MAN, KLEY/KLEY HERTZ→KLE).
- Procura na 1ª descrição primeiro; nome em qualquer lugar, código só como **última palavra**.
- Achou → é o fabricante. Se o arquivo trouxe outro → alerta "Arquivo: fabricante X difere do laboratório na
  descrição (Y); usado Y". Não achou → fabricante do arquivo; sem ele, o da marca.
- Laboratórios do grupo saem pelo grupo (Germed e Legrand → EMS PHARMA; Neo Química → HYPERA PHARMA) — confirmado.

### 3.5b Base de marcas de Farmácia do cliente (`dados/farma_marcas/`)
- Exportação "Hoja" (fabricante, Marca, Est Mer 6/7, venda 24 meses). `python3 farma_marcas.py` → `consts.json`:
  `farmaMarcas` (marca comercial sem o código do laboratório → EST MER 7 de maior venda → categoria do app, fabricante)
  e `farmaCodLab` (código de 3 letras → laboratório, depois dos códigos aprendidos da DIMA). Linha de genérico
  ("OMEPRAZOL TEU") só ensina o código do laboratório.
- Categoria: marca comercial da base decide a categoria antes do princípio ativo (quando as regras deram Farmácia, nada
  ou PET sem animal); marca de 2+ palavras ganha até de categoria de outra cesta (LEITE MAG PHILLIPS). Alerta
  "Categoria pela marca X"; vai para revisão quando a marca aparece em mais de uma EST MER 7.
- As colunas EST MER 6/7 também alimentam os nomes oficiais (268 de 400 com código agora).
- Arquivo atual: Hoja 1 46 (capítulo A — digestivo/metabolismo, 1.881 linhas). Mais arquivos: pôr na mesma pasta e rodar
  `python3 nomes_oficiais.py && python3 farma_marcas.py && python3 build.py`.
- Teste `node testes_farma/rodar_hoja.js` (1.522 marcas do arquivo como descrições sintéticas): marca certa 1.329,
  fabricante certo 1.428, em Farmácia 1.481 (antes: 870 / 802 / 412); genéricos 239 de 243. Erros em
  `testes_farma/hoja_erros.txt` — boa parte é a DIMA dando outra grafia (CLAZI x CLAZI XR), marca com nome de laboratório
  (SANDOZ, JANSSEN) e 3 EST MER 7 que não existem no app (A03E OUTRAS ASSOCIACOES, A11A1/A11B1 PRENATAL).

### 3.5c Categoria pela DIMA (ATC EphMRA, todos os capítulos)
- `python3 farma_dima.py`: cada marca/substância de Farmácia da DIMA (nome sem o código do laboratório) → EST MER 6 mais
  votada → categoria do app (EST MER 7 com esse código; várias: associação x pura, marcada para revisão; sem código no
  app: tabela `MAPA6`). EST MER 6 sem nenhuma categoria no app vira categoria nova (13: H02A CORTICOSTEROIDES PUROS,
  D07B ASSOCIACOES DE CORTICOIDES, C05A ANTIHEMORROIDARIOS TOPICOS…). ~4.800 termos em `consts.json → farmaDima`.
- Ordem da categoria: base de marcas do cliente (Hoja) > dicionário de princípios ativos > regras do manual (palavras-
  chave) > DIMA. Termo de uma palavra só da DIMA vale no começo da descrição ou com sinal de remédio (MG, COMP, GOTAS,
  código de laboratório no fim). Palavra comum/de outra cesta não vira termo. Código de laboratório no fim
  (`ANLODIPINO … BIS`) não deixa a marca de alimento (BIS) ganhar.
- Alerta "Categoria pela DIMA: X em EST MER 6"; vai para revisão quando a subcategoria foi escolhida ou a marca está
  dividida entre EST MER 6.
- Teste `node testes_farma/rodar_dima.js` (2.000 marcas de Farmácia da DIMA como descrições): OUTRA CATEGORIA
  1.167 → 124; em Farmácia 794 → 1.847; EST MER 6 certa 581 → 1.476; fabricante certo 1.770 → 1.886. 3.000 descrições
  reais de papelaria/material: nenhuma mudou. Os "erros" restantes incluem erros da própria DIMA (METOPROLOL em C09C).

### 3.5d Descrições das lojas (arquivo "Desc. SKU Min.")
- Campo "Descrições das lojas" na tela: SKU x loja x "Descripcion Minorista". Para cada SKU o app escolhe a descrição
  mais completa (`notaDesc`: quantidade C/30 · 30 CPR · 10ML, dosagem, forma, laboratório/GEN no fim, quantas lojas
  usam, tamanho; cortada no fim perde ponto). Ela vira a descrição principal; as do backlog e as outras lojas ajudam na
  votação. Sem backlog, o arquivo das lojas vira o backlog.
- Limpeza das lojas (`desgruda`): marca colada no "C/" (`FLUIMUCILC/16` → `FLUIMUCIL C/16`), letra colada no número
  (`MILD10ML` → `MILD 10ML`), prefixo ZZ de descontinuado (`ZZLECTRUM` → `LECTRUM`).
- REVISAO ganhou DESCRICAO DA LOJA USADA e LOJAS (quantas linhas de loja o SKU tem).
- Dosagem combinada pelo texto original: `2+1MG`, `3+3MG/ML`, `50+170MCG/DIA`, `400MCG+10MG`.
- Teste `node testes_farma/rodar_lojas.js dados/lojas/Desc_SKU_Min_2592026_1.csv [backlog]`: backlog só com o nome
  (`testes_farma/lojas_backlog_curto.csv`) dava 65/65 SKUs em 1UN; com o arquivo das lojas, 1 (ZOLADEX, injeção única)
  e 3 em OUTRA CATEGORIA (SUPREMA, STER MD, ENVID: não estão em nenhuma base).
- Correções vindas desse arquivo: corticoide sozinho (dexametasona, prednisona…) → H02A CORTICOSTEROIDES PUROS;
  colírio → S01B; dexametasona creme → D07A; "VITA E" = vitamina E; vitaminas de marca da DIMA (EPHYNAL, EMAMA) →
  VITAMINA OUTRO; marca com nome da empresa (SANDOZ, GEOLAB) não decide categoria; EURO = Eurofarma; DIA não é marca.

### 3.5e Quantidade (menos 1UN)
- A limpeza de grafia colada vale também para o backlog: `MILD10ML`, `SOLUSPAN1ML`, `MD10ML`, `N40GR` (letra colada em
  número com unidade), `CONTIC/8` (marca colada no C/), `ZZ` de descontinuado.
- Contam como unidade: COMPS, CPRS, FLACONETE(S), AMPOLA(S), SACHE(S), ENV/ENVELOPE(S), SERINGA(S), GOMA(S), ADES/
  ADESIVO(S), OVULO(S), SUPOSITORIO(S), PASTILHA(S), TABLETE(S), BISNAGA(S), FRASCO(S). Cartela: `3X21 CPR` = 63.
- Genérico gravado na DIMA com o laboratório (`ACECLOFENACO EMS`): marca = a substância.
- Teste `testes_farma/formatos_farmacia.csv` (147 descrições reais e formatos comuns): 1UN 20 → 4 (3 são 1 unidade
  mesmo: ZOLADEX, 1 AMPOLA, 1 SERINGA; 1 é descrição cortada "ACECLOFENACO 10").

### 3.5f Descrição no padrão Anvisa
- `VERZENIOS 50 MG COM REV CT BL AL AL X 30`: COM depois da dose ou antes de REV/EFERV/MAST/SUBL… = comprimido
  ("COM 12" continua sendo "com 12"); `X 30` é a quantidade quando há forma que se conta (comprimido, cápsula, sachê…);
  embalagem (CT, BL, AL, PLAS, OPC, TRANS, INC, AMB, VD, BG, TB, PVC…) sai do descritivo; SUS OR = SUSPENSAO ORAL,
  GOT = GOTAS, CREM DERM = CREME DERMATOLOGICO, LIB = LIBERACAO.
- A ordem das partes não importa: "COM" é comprimido antes de REV/EFERV/MAST…, antes de "X 24", antes da dose
  ("COM 100 MG") ou em qualquer lugar quando a descrição tem cara de Anvisa (REV, EFERV, CT, BL…); "COM 12" continua
  "com 12". Teste com 32 ordens da mesma descrição (`testes_farma/ordens_anvisa.csv`): todas 24UN.
- Dose em G antes da forma (`VITAMINA C 1 G COMP EFERV … X 10`): o conteúdo é a contagem (10), não 1G.
- Resultado: `VERZENIOS REVESTIDO 50MG 30CPRS` (antes 1UN). Exemplos em `testes_farma/anvisa_formatos.csv`.

### 3.5g Lista CMED/Anvisa (embutida) e número solto
- `dados/cmed/` (PMC - xls da Anvisa, 26 mil apresentações) → `python3 cmed.py` → `cmed.json.gz` (0,4 MB), embutido pelo
  `build.py`. Na tela (etapa 3) dá para anexar uma lista mais nova, que substitui a embutida.
- Código de barras na CMED: a descrição oficial (PRODUTO + APRESENTAÇÃO, ex. `VERZENIOS 50 MG COM REV CT BL AL AL X 30`)
  vira a principal (quantidade oficial); o laboratório da CMED vira o fabricante quando a descrição não traz outro; a
  CLASSE TERAPÊUTICA (EphMRA "L1H", "M1A1" → L01H, M01A1) decide a categoria quando o app deu outra cesta ou outro grupo
  ATC. Produto de marca (não genérico): marca = nome do produto (DTN FOL, NATIFA PRO UBD).
- Sem código de barras: o nome do produto/substância da CMED dá a categoria oficial (depois da base do cliente, do
  dicionário e das regras; antes da DIMA), e as apresentações que existem do produto validam o número solto.
- `python3 cmed.py --baixar` baixa do site da Anvisa a lista PMC mais nova e os dados abertos de medicamentos
  registrados (DADOS_ABERTOS_MEDICAMENTOS.csv). Os registrados que não estão na lista de preços (~10,5 mil nomes) entram
  como nome → princípio ativo → categoria (dicionário do cliente, ou classe que a substância tem na CMED). Vêm depois da
  DIMA e só valem com sinal de remédio na descrição (dose, forma, laboratório). Alerta "Categoria pelo registro Anvisa".
- Número solto (`ACEFLOR 24 REV CT BL AL PLAS OPC 100 MG`): em Farmácia, número sem unidade que não é dose e é tamanho de
  caixa comum (ou apresentação da CMED do produto) vira a contagem, com alerta.
- Backlog só com o nome (`testes_farma/lojas_backlog_curto.csv`), sem arquivo das lojas: 1UN 65 → 1 e OUTRA CATEGORIA 5 → 0
  só com a CMED embutida.

### 3.6 Marca
- Regra (decidida): **nome comercial**; genérico → **princípio ativo** como marca (como escrito na descrição: LOSARTANA,
  DIPIRONA), fabricante = laboratório.
- Ordem: marca comercial da DIMA/dicionário (descartando laboratório, GENERICO e nome com princípio ativo — a DIMA tem
  `EMS`, `CIM`, `LOSARTANA POTASSICA`, `DIPIRONA`/BIOVET); senão a 1ª palavra da descrição, se não for princípio ativo,
  sal, forma, número ou laboratório (só em categorias sem início fixo); senão o princípio ativo; senão OUTRA MARCA.
- Marca do arquivo que é laboratório/genérico é trocada, com alerta.
- A DIMA grava a marca com o código do laboratório (`DORFLEX (OPE)`, `NEOSALDINA HYP`). O `dima.py` cria também o
  nome sem o código nas categorias ATC (só marca comercial, nunca nome com princípio ativo), e o nome comercial achado na
  descrição busca o fabricante na DIMA e depois no dicionário: DORFLEX → OPELLA, NEOSALDINA → HYPERA PHARMA,
  TYLENOL → KENVUE.

---

## 4. Pendências para o agente de Farmácia
1. **Nomes oficiais** das 132 categorias sem código (pedir a árvore EST MER 7/6 com códigos). A base traz
   `C10A1 ESTATINASINIB DA HMG COA REDUTASE` (parece "ESTATINAS/INIB…" sem a barra) — confirmar.
2. Validar com o cliente as **correções** da base (3.1) e as 455 linhas marcadas VALIDAR.
3. Confirmar abreviações das formas na quantidade (CPRS, CAPS, DRGS) e se GENERICO deve sair do descritivo.
Resolvidas: marca (3.6), dosagem no descritivo (3.3), laboratórios pelo grupo (3.5), CORTICOIDES = S01B.

## 5. Resultados de referência (testes)
Ver `testes_farma/resultados.txt` (gerado por `node testes_farma/rodar.js`). Exemplos:
- `DIPIRONA SODICA 500MG C/10 CPR EMS` → N02B NAO NARCOTICOS ANTIPIRETICOS · marca DIPIRONA · EMS PHARMA ·
  "DIPIRONA SODICA 500MG 10CPRS"
- `LOSARTANA POTASSICA 50MG 30 COMP GERMED` → C09C ANTAGONISTAS DE LA ANGIOTENSINA II PUROS · marca LOSARTANA ·
  fabricante EMS PHARMA · "LOSARTANA POTASSICA 50MG 30CPRS"
- `DORFLEX DIPIRONA 300MG 10 COMP` → marca DORFLEX · fabricante OPELLA · "DORFLEX DIPIRONA 300MG 10CPRS"
- `OMEPRAZOL 20MG 28 CAPS NEO QUIMICA` → fabricante HYPERA PHARMA
- `CETOCONAZOL CREME 30G` → ANTIFUNGICOS DERMATOLOGICOS TOPICOS; `CETOCONAZOL 200MG 10 COMP` → antimicóticos sistêmicos
- `AMOXICILINA 250MG P/ CAES E GATOS` → não vai para Farmácia humana
