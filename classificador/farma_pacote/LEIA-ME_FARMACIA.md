# Farmácia — tudo o que foi definido até aqui (Classificador de Backlog)

Pacote para continuar o trabalho de **Farmácia** em outro chat/agente. O app é o `classificador.html`
(link publicado: https://claude.ai/artifact/UFuhJCnyT5Lwi3wYZVMVu1; código-fonte no repositório
`marcato-app/felipefreitas`, pasta `classificador/`, branch `claude/modest-maxwell-y0utos`).

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
> 3. **Descritivo** — começa pela **marca**; sem marca, pelo **princípio ativo**; só as categorias com abreviação fixa
>    no manual (ex.: `SUPL ALIM`, `SUPL ALIM POLIV`, `CURATIVO`) começam pela abreviação. Nunca pelo nome da
>    categoria. Forma farmacêutica por extenso: COMP/CP/CPR = COMPRIMIDO, CAPS = CAPSULA, DRG = DRAGEA, SUSP =
>    SUSPENSAO, XPE = XAROPE, GTS = GOTAS, POM = POMADA… (nunca "COMPOSTO").
> 4. **Conteúdo** — sempre com unidade. Formas farmacêuticas contam como unidade (`30 COMP` → 30UN, `C/10 CPR` →
>    10UN, `30 DRG` → 30UN); líquidos/cremes em ML/G (`COLIRIO 5ML`, `CREME 30G`). Sem nada: 1UN.
> 5. **Prioridade do arquivo** — categoria, marca, fabricante e conteúdo que vierem no arquivo valem; só trocar o que
>    estiver bem fora do comum, **sempre com alerta** (ex.: fabricante do arquivo diferente do laboratório escrito na
>    descrição → vale o laboratório). O descritivo é sempre padronizado.
> 6. A regra "marca só vale se existir na EST MER 6 do item" (usada nas outras cestas) **não** se aplica à Farmácia.
> 7. Pendências a resolver com a pessoa: regra de **marca** na Farmácia; nomes oficiais que faltam; CORTICOIDES.

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
- **CORTICOIDES** é ambíguo: R03D (respiratório) ou S01B (oftalmológico) — perguntar.

### 3.3 Descritivo
- Categoria sem início fixo no manual (379 de 400): **marca** na frente; sem marca, **princípio ativo** (como está
  escrito na descrição); sem nenhum, o nome do produto.
- Categorias com início fixo mantêm (SUPL ALIM, SUPL ALIM POLIV, SUPL ALIM MULT, CURATIVO, LUVA DE PROCEDIMENTO,
  SORO FISIOLOGICO, AGUA OXIGENADA…).
- Abreviações de forma: COMP/COMPR/CP/CPR/CPS = COMPRIMIDO; CAP/CAPS = CAPSULA; DRG = DRAGEA; SOL = SOLUCAO; SUSP =
  SUSPENSAO; XPE/XAR = XAROPE; GTS = GOTAS; POM = POMADA; AMP = AMPOLA; INJ = INJETAVEL; EFERV = EFERVESCENTE;
  REV = REVESTIDO.
- Ainda **não** sai a dosagem (500MG) no descritivo — confirmar se o padrão exige.

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
- Observação: as bases registram marcas do grupo pelo grupo (Germed e Legrand saem EMS PHARMA; Neo Química sai
  HYPERA PHARMA). Se o cliente quiser o laboratório "de rótulo", mudar os apelidos.

### 3.6 Marca
- Hoje: DIMA primeiro, depois dicionário; na Farmácia **sem** exigir que a marca exista na EST MER 6 do item.
- **Pendente**: a DIMA registra "marcas" como `CIM`, `EMS`, `LOSARTANA POTASSICA` (genérico + laboratório). Falta a
  regra: genérico sai com o laboratório como marca? medicamento de marca (DORFLEX, NEOSALDINA) com o nome comercial?

---

## 4. Pendências para o agente de Farmácia
1. Regra de **marca** na Farmácia (item 3.6).
2. **Nomes oficiais** das 162 categorias sem código (pedir a árvore EST MER 7/6 com códigos).
3. **CORTICOIDES**: R03D ou S01B?
4. Validar com o cliente as **correções** da base (3.1) e as 455 linhas marcadas VALIDAR.
5. Dosagem (MG) no descritivo: sim ou não?
6. Apelidos de laboratório: grupo (EMS/HYPERA) ou laboratório de rótulo (GERMED/NEO QUIMICA)?

## 5. Resultados de referência (testes)
Ver `testes/resultados_esperados.txt`. Exemplos:
- `DIPIRONA SODICA 500MG C/10 CPR EMS` → NAO NARCOTICOS ANTIPIRETICOS (oficial N02B …) · EMS / EMS PHARMA ·
  "EMS DIPIRONA SODICA COMPRIMIDO 10UN"
- `LOSARTANA POTASSICA 50MG 30 COMP GERMED` → C09C ANTAGONISTAS DE LA ANGIOTENSINA II PUROS · fabricante EMS PHARMA ·
  "LOSARTANA POTASSICA COMPRIMIDO 30UN"
- `OMEPRAZOL 20MG 28 CAPS NEO QUIMICA` → fabricante HYPERA PHARMA
- `CETOCONAZOL CREME 30G` → ANTIFUNGICOS DERMATOLOGICOS TOPICOS; `CETOCONAZOL 200MG 10 COMP` → antimicóticos sistêmicos
- `AMOXICILINA 250MG P/ CAES E GATOS` → não vai para Farmácia humana
