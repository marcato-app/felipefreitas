# Classificador de Backlog — handoff para Claude Code

Artifact publicado (versão 14, já com o fix abaixo): https://claude.ai/artifact/UFuhJCnyT5Lwi3wYZVMVu1

## O que é

App client-side (HTML+JS puro, sem servidor) que classifica planilhas de SKU:
- categoriza cada item por regras de palavra-chave (incluir/tambem/excluir/forte/pctMin)
- decide marca/fabricante batendo contra um dicionário de marcas
- extrai conteúdo/quantidade (g, ml, UN, packs)
- monta um "DESCRITIVO PADRONIZADO" por item
- exporta tudo em .xlsx (aba principal + aba de revisão)

Tem um botão "Aplicar regras com Claude" que usa `window.claude.use(...)` (API do Cowork) pra transformar texto livre em regras. **Isso só funciona dentro do Cowork/claude.ai** — no Claude Code local você não vai ter esse botão funcionando (ele vai cair no fallback e dar erro/nada), mas o resto do app roda 100% offline no navegador.

## Arquivos deste pacote

- **`src.html`** — fonte editável (tem o placeholder `/*CONSTS*/null` onde os dados são injetados, e `claude.use(` sem o wrapper `cuse`).
- **`consts.json`** — todos os dados: listas de palavras (GENERIC, NOISE, ATTR, FLAVORS, TOK...), as ~40 categorias de alimento feitas à mão (`cfg.categorias`) e a biblioteca de 1.569 categorias convertidas do manual do cliente (`libSeed.categorias`), organizadas em 13 "cestas" (PERECIVEIS, MERCEARIA, FARMACIA, BAZAR, etc).
- **`classificador.html`** — o app já **construído** (src + consts injetados), pronto pra abrir direto no navegador. É o mesmo conteúdo publicado no artifact.
- **Script de build** (caso edite `src.html` ou `consts.json` e precise gerar o `classificador.html` de novo):
  ```python
  import re
  s = open('src.html').read()
  s = s.replace("claude.use(", "cuse(").replace(
      "const OUT = 'OUTRA CATEGORIA';",
      "const OUT = 'OUTRA CATEGORIA';\nconst cuse = n => (window.claude && typeof window.claude.use === 'function') ? window.claude.use(n) : Promise.resolve(null);",
      1)
  s = s.replace('/*CONSTS*/null', open('consts.json').read())
  open('classificador.html', 'w').write(s)
  ```
  Depois só abrir `classificador.html` no navegador (ou `python3 -m http.server` na pasta).

## Histórico do bug "PRODUTO na frente de tudo"

1. **1ª causa (resolvida)**: para itens que caem em "OUTRA CATEGORIA", a função `nounOutra()` tentava achar um substantivo real na descrição do item e, quando falhava, devolvia o literal `'PRODUTO'`. Reescrevi ela pra escanear todas as descrições (não só as 3 primeiras), tratar prefixos de código interno colados (`003MINI` → `MINI`) e relaxar a lista de "ruído" em camadas antes de desistir. Isso derrubou de 126 → 27 itens "PRODUTO" no arquivo de teste (52.983 linhas).

2. **2ª causa, bem maior (resolvida agora)**: ao converter as 1.569 categorias do manual do cliente, o campo "início do descritivo" foi extraído literalmente do padrão `PRODUTO | MARCA | ...`. Só que "PRODUTO" e "MARCA" ali eram **placeholders genéricos** do template ("insira aqui o nome do produto" / "insira aqui a marca"), não texto fixo. Isso deixou **244 categorias** (incluindo `PAPELARIA OUTROS`, pra onde cai a maioria dos itens de papelaria) com "PRODUTO" travado como prefixo fixo, e **370 categorias de Farmácia** com "MARCA" travada. Corrigido em `consts.json`: essas categorias agora têm `inicio: ""` (e as 244 ganharam `dinamico: true`, que faz o `runAll()` extrair o nome do produto dinamicamente por item, igual já fazia pra OUTRA CATEGORIA).

3. **3ª causa, a que ainda estava incomodando (resolvida agora)**: o app guarda a "biblioteca" de categorias no `localStorage` do navegador (e opcionalmente num DB), e o merge que traz atualizações da biblioteca embutida no código é em modo **`add`** — só adiciona categorias que ainda não existem pro usuário, **nunca sobrescreve** uma categoria que ele já tinha salva. Ou seja: quem já tinha usado o app antes desse fix ficou com a versão *quebrada* de `PAPELARIA OUTROS` (e das outras 613) presa pra sempre no navegador, e a correção no `consts.json` nunca chegava até ela. É por isso que só caiu de 40 mil pra 38 mil da primeira vez — a maior parte dos itens continuava usando a categoria antiga salva localmente.

   Fix: adicionei uma migração que roda uma vez no carregamento (logo depois do `mergeInto`), varrendo **todas** as categorias já salvas do usuário e corrigindo direto qualquer `inicio` que seja literalmente `"PRODUTO"` ou `"MARCA"` — sem mexer em mais nada da categoria (incluir/excluir/ativa/etc ficam intactos). Está em `src.html`, função `migrarInicioPlaceholder()`, chamada logo antes do `renderCats()` final.

   Testado simulando exatamente esse cenário (um "draft antigo" no localStorage com a categoria quebrada) e confirmando que a migração conserta e o resultado final bate com o teste "do zero": **27 itens com PRODUTO em 52.983** (todos ruído de dado real tipo `"PRODUTO NAO CAD"`, que já vinha assim na descrição original).

## Se ainda aparecer "PRODUTO" depois disso

Pontos pra checar, em ordem:
1. **Cache do navegador / aba antiga aberta** — force reload (Ctrl+Shift+R) ou abra em aba anônima.
2. **`localStorage` não foi tocado** — a migração só roda quando a página carrega o script inteiro; se estiver testando com `page.evaluate` direto sem recarregar, ela não dispara.
3. Rodar o grep abaixo pra achar qualquer categoria que ainda tenha `inicio` literal quebrado (a migração cobre "PRODUTO"/"MARCA" exatos, mas se o manual tiver outro placeholder tipo "PRODUTO/MARCA" junto ou variações, não pega):
   ```bash
   python3 -c "
   import json
   c = json.load(open('consts.json'))
   for x in c['libSeed']['categorias'] + c['cfg']['categorias']:
       ini = (x.get('inicio') or '').strip()
       if ini and ini in ('PRODUTO','MARCA', 'PRODUTO/MARCA'):
           print(x['nome'], repr(ini))
   "
   ```
4. Testar direto com Playwright abrindo `classificador.html`, subindo o backlog real, clicando `#btnRun` e contando quantos `data.results` têm `.desc` começando com `"PRODUTO "` — é o método usado pra validar tudo acima (scripts de exemplo ficam em `t14.js`/`t15.js`/`t16.js`, se quiser levar o padrão).

## Outras coisas implementadas nesta sessão (pra contexto)

- Persistência de biblioteca (categorias ficam salvas entre usos, nunca apagadas — só desativadas).
- Quantidade padrão (ex.: "1UN") quando nada é encontrado na descrição, e parsing de contagem por unidade (C/30, 6UN, DZ) pra ovos e afins.
- Coluna **CODIGO INTERNO** no export, implementando a fórmula Excel do cliente (função `ciFlag()`):
  ```
  =SE(ESQUERDA(E3;7)="3910000";"Código Scanntech";
     SE(OU(E(NÚM.CARACT(E3)<=6;E3>0);ÉNÚM(LOCALIZAR("00000";E3)));
        "Possível Código Interno";"Sem indícios de CI"))
  ```
- Remoção de códigos ATC vazados nos nomes de 383 categorias de Farmácia.

## Princípio ativo (Farmácia)

- Base: `dados/dicionario_nomenclaturas_farmaceuticas.xlsx` (Scanntech). `python3 farma_pa.py` converte para `consts.json → farmaPA`; depois `python3 build.py`.
- Regra (`compilePA`/`matchPA`/`classifyDesc` em `src.html`): se a descrição tem um princípio ativo da base e a categoria dele está ativa, ela decide a categoria quando as regras normais deram Farmácia, nada, ou PET sem palavra de animal. Categoria de outra cesta que bateu pelas regras (shampoo com cetoconazol, bicarbonato culinário) continua valendo. Itens com CAO/GATO/PET/VET não são puxados para Farmácia.
- Combinações e formas exigem todas as partes (AMOXICILINA+CLAVULANATO; TIMOLOL + COLIRIO; CETOCONAZOL + CREME…); a mais específica ganha, e no empate vale o princípio que aparece primeiro.
- Princípio em mais de uma classe: destino em `PRIMARIA` no `farma_pa.py`. Erros evidentes da base (vitaminas A/D/E/K em "VITAMINA B1" etc.) estão em `CORRECOES`.
- Alerta "Categoria pelo princípio ativo X" em todo item decidido assim; vai para a aba REVISAO só quando a base marca VALIDAR ou o destino foi corrigido.

## Tipo do produto na frente + vocabulário de material (MATERIAL OUTROS)

- `classifyRules`: além da regra antiga (1ª categoria pela prioridade), olha a **1ª palavra "de verdade"** da descrição (`headPos`: pula códigos de embalagem `SKIPTIPO` — ENCART, ENC, UTIL… —, números e marcas do dicionário). Categoria que bate exatamente nela ganha quando a regra antiga bateu mais para o meio do texto por outra palavra — exceto se a categoria antiga também fala daquele tipo (termos ou nome começando com ele: BISCOITO AGUA E SAL, CHOCOLATE TABLETE). Empate na 1ª palavra: termo mais longo ganha.
- Nova lista por categoria, **`tipo`**: palavras soltas que só valem como 1ª palavra (FIO, PORTA, PINO, RALO…), para não pegarem "PORTA RETRATO", "LIMA" (fruta) etc. Termos em `tipo` também desligam o mesmo termo em "sempre OUTRA CATEGORIA".
- `vocab_material.py` gera os termos (tipos, frases, exclusões e termos genéricos removidos, como BRANCO em ARROZ BRANCO e ROSCA em FARINHA ROSCA) em `consts.json` e em `libPatch`, que `migrarCategorias()` aplica uma vez nas categorias salvas no navegador (a lista `tipo` é garantida sempre).
- Resultado no backlog de 12.367 itens de MATERIAL OUTROS (`dados/material_outros_revisao.xlsx`): OUTRA CATEGORIA 8.184 → 2.269; itens em construção/ferramenta 908 → 7.591.
- Farmácia sem início fixo no manual: o descritivo começa pela marca ou, sem marca, pelo princípio ativo; COMP/CP/CPR = COMPRIMIDO; formas farmacêuticas contam como unidade.

## Vocabulário de papelaria (PAPELARIA OUTROS)

- `vocab_papelaria.py` (rodar depois do `vocab_material.py`, a partir do consts sem patches): tipos de papelaria/armarinho/festa, falsos positivos (TNT → energético, AZ → azeitona, GLITTER TUBOS → tubo…), e `remover_tipo`/`remover_excluir` para tipos do material que eram de papelaria (LINHA, LETRA, BOBINA, GRAMPEADOR, ESTILETE) e exclusões que criavam buraco (PAPELARIA OUTROS excluía LAPIS; LAPIS excluía APONTADOR/BORRACHA).
- Patches agora ficam em `consts.json → libPatches[id]`; `migrarCategorias()` aplica cada um uma vez nas categorias salvas (tipo sempre).
- Categoria dinâmica (PAPELARIA/MATERIAL OUTROS…): o descritivo começa pelo tipo que decidiu a categoria (`tipoIni`), mesmo que ele esteja na lista de ruído (ex.: ESTOJO).
- Backlog de 29.131 itens (`dados/papelaria_outros_revisao.xlsx`): OUTRA CATEGORIA 12.278 → 2.565.

## Base de marcas DIMA (marca antes do dicionário)

- `dados/DIMA_Peso_Fixo.xlsx` → `python3 dima.py` → `dima.json.gz` (1,4 MB), embutido pelo `build.py` em base64 (`/*DIMA*/null`). Carregado ao abrir a página (`loadDima`, DecompressionStream).
- Abas: Mapeio (categoria EST MER 6 × marca × fabricante, 175 mil linhas), Abreviaturas (apelidos → mesma marca), Sheet3 (padrão OUTRA MARCA por categoria — é só o valor padrão; não trava marca, porque lista CERVEJA, REFRIGERANTE… que têm marca).
- `runAll`: marca/fabricante procurados primeiro na DIMA; o dicionário enviado só entra se a DIMA não achar nada (`brandDicts()`).
- Para a DIMA não virar "marca" de palavra comum: sem apelido pela 1ª palavra (`dictFinish(dict, true)`); o tipo do produto (1ª palavra) nunca é marca; palavra do vocabulário da categoria ou da lista `tipo` só é marca se não houver outra candidata e a DIMA tiver a marca numa categoria de nome parecido (`segParecido`); `MARCA_NAO` (INOX, METAL, MULTI USO…).
- Sem dicionário enviado: alimentos 50/60 com marca (os 10 restantes são itens sem marca ou NINHO, que já era palavra genérica); papelaria 19.047/29.131; material 7.751/12.367.

## Código com descrições de produtos diferentes (ex.: ESTOJO + OVOS + PNEU)

- `coerentes()` em `aggregate`: a referência é a 1ª descrição (ou a coluna de descrição principal do backlog — DESCRIPCION/DESCRICAO/DESCRITIVO…, se existir, vai para o 1º lugar). Descrições sem nenhuma palavra em comum com a referência (igual ou prefixo ≥4 letras, ignorando números, códigos de embalagem, atributos) não votam na categoria nem entram em marca, quantidade e descritivo. Alerta "Descrições de produtos diferentes no mesmo código" (prioridade 1 na revisão).
- Não usar "maioria" como referência: no backlog de papelaria as duas descrições de fora muitas vezes são do mesmo produto errado.
- Papelaria com as 3 descrições (Descripcion + TOP + MAX): itens com tipo diferente do da descrição principal 1.197 → 837 (de 26.719).

## Marca só vale se existir na categoria EST MER 6 (fora da Farmácia)

- Referência é sempre a EST MER 6 (nível da DIMA e do dicionário). `segmentos.py` gera `consts.json → segPadrao` (categoria → EST MER 6): mapa fixo (construção, papelaria…), nome idêntico, 1ª(s) palavra(s) = categoria DIMA, Farmácia pelo dicionário de princípios ativos. Hoje 733/1569 ligadas.
- `segmentosEstMer6()` no `runAll`: 1º o campo "Segmentos" da categoria (fixado à mão ou calculado do backlog), 2º `segPadrao`, 3º aprendido na hora (EST MER 6 das marcas achadas nos itens da categoria, ≥3 itens, fatia ≥20%; em `data.segAprendido`).
- Com a EST MER 6 conhecida, a marca tem que existir nela: DIMA primeiro; se não achar, dicionário com a mesma regra. Fabricante = maior venda da marca dentro da EST MER 6 (DIMA: mais frequente). EST MER 6 normalizada (acento/maiúscula).
- Farmácia fica de fora (`seg.livre`): regra própria de fabricante, a definir.
- `dados/marcas_por_categoria_revisao.xlsx`: antes × agora nos três backlogs de teste.

## Prioridade do arquivo (backlog manda)

- Opção "Priorizar os dados do arquivo" (`cfg.priorizarArquivo`, ligada por padrão). Categoria, marca, fabricante e conteúdo do backlog valem; o app só troca o que estiver bem fora do comum, sempre com alerta "Arquivo: …":
  - categoria: nenhuma descrição bate com ela E a descrição aponta para outra cesta (`categoriaArquivo`);
  - marca: não aparece em nenhuma descrição E a descrição traz outra marca que existe na EST MER 6 do item;
  - fabricante: a base conhece a marca e o fabricante do arquivo não é nenhum dos dela (Farmácia: fica o do arquivo);
  - conteúdo: a descrição tem outro valor na mesma unidade com mais de 2× de diferença;
  - descritivo: NÃO vem do arquivo; é sempre padronizado pelo app, já com os valores mantidos acima (a coluna de descritivo do arquivo, se houver, só entra como descrição de referência).
- Campo vazio no arquivo: o app completa como antes. Aba REVISAO ganhou FABRICANTE SUGERIDO.

## Nome oficial das categorias (código EST MER 7/6)

- Uma limpeza antiga tirou o código ATC do nome de ~380 categorias de Farmácia. O nome interno ficou (regras/ligações/navegador dependem dele); `nomes_oficiais.py` gera `consts.json → nomesOficiais` (interno → oficial, ex.: "ANTAGONISTAS H2" → "A02B1 ANTAGONISTAS H2") a partir do dicionário de princípios ativos e da DIMA, e conserta nomes corrompidos (hífen sobrando, acento quebrado). 238/400 de Farmácia recuperados; lista em `dados/farma_nomes_oficiais.xlsx`. Com a árvore oficial em `dados/arvore_est_mer.xlsx`, rodar de novo.
- `nomeOf()` é o que sai na planilha (Planilha1, REVISAO, RESUMO) e na tela; `catInterna()` reconhece a CATEGORIA do arquivo pelo nome oficial (com ou sem código) ou interno. Categoria pode ter `nomeOficial` próprio (sobrepõe).
- Conteúdo do arquivo só com número: unidade pela contagem da descrição ou pela `unidadeSugerida` da categoria.

## Farmácia: fabricante = laboratório da descrição

- `labIndex()` (refeito ao carregar DIMA/dicionário): fabricantes de categorias ATC (dicionário primeiro, depois DIMA) → nome completo sem LTDA/FARMA/PHARMA… como termo; códigos de 3 letras aprendidos do fim das marcas de Farmácia ("DOMPERIDONA RAN" → RANBAXY; ≥3 ocorrências e ≥80% do mesmo fabricante); `LAB_ALIAS` para nomes de laboratório que as bases registram pelo grupo (GERMED/LEGRAND → EMS PHARMA via GER/LEG; NEO QUIMICA → HYPERA via NEO; PRATI → PRD…).
- `labDaDescricao()`: 1ª descrição primeiro; nome em qualquer lugar, código só como última palavra. Nunca usa só a 1ª palavra do nome do fabricante (PONTO DAS ERVAS pegava "LV PONTO").
- Em item de Farmácia, o laboratório achado vira o fabricante (grafia do dicionário quando anexado); se o arquivo trouxer outro fabricante, alerta "Arquivo: fabricante X difere do laboratório na descrição". Sem laboratório: fabricante do arquivo ou da marca.
- Geral: item sem marca agora mantém o fabricante do arquivo (antes virava OUTRO FABRICANTE).

## Sempre uma unidade de medida

- Depois de descrição, arquivo e padrão da categoria: sem quantidade nenhuma → 1KG se a descrição diz KG/KILO/GRANEL sem número (vendido a quilo), senão 1UN; número sem unidade → UN. Alerta "Sem quantidade na descrição; usado o padrão …".

## Conteúdo: o que parece quantidade mas não é

- `conv()`: por unidade até 60 kg / 60 L (`QMAX`); acima é código/capacidade. "K" solto só é quilo com número ≤ 50 ("7830K" é modelo).
- `textoQtd()` (texto só para ler quantidade): gramatura de papel (40–450 G com PAPEL/CARTOLINA/A4/FLS…) é ignorada; capacidade depois de P/PARA (colado no número ou com PANELA/PRESSAO/FREEZER/LIXO/BALDE/GALAO…) é ignorada; folhas (FLS/FOLHAS/F) contam como UN só em produto de papel (caderno, bloco, agenda, sulfite, refil…), nunca em grampeador/perfurador/janela, e só se não houver contagem em UN.
- Cestas que não são de consumo (BAZAR, CONSTRUCAO, TEXTIL, ELETRO; OUTRA CATEGORIA com contagem ≥ 100): peso/volume solto + contagem ≥ 20 → conteúdo é a contagem ("CARTUCHO 2KG C/500" → 500UN, "BOBINA FREEZER 3KG C/50" → 50UN).
- Aviso "Conteúdo fora do comum para a categoria (típico …)": peso/volume >20× ou <1/20 da mediana da categoria no backlog (≥ 5 itens). Só avisa.
- `dados/conteudo_revisao.xlsx`: o que mudou e o que foi avisado nos backlogs de teste.

## Objeto nunca recebe peso/volume como conteúdo

- `U` não tem mais "K" solto (7830K, 4K são modelo). "2K" só vira 2KG em texto com substância vendida a peso (`SUBST_RX`: barbante, grampo, prego, arame, tinta, cola…), número ≤ 50.
- `vendidoPorUnidade()`: categoria de objeto (nome com ESCOVA, PENTE, TESOURA, ALICATE, ESPELHO, ACESSORIO…, `DURAVEL`, sem substância na descrição) ou tipo do produto (1ª palavra) em `OBJETO_TIPO` (regador, pulverizador, copo, régua, estojo, prumo, lona, sacola, bobina, lixa, borracha, caixa, filtro, tanque…) → peso/volume da descrição não é conteúdo; fica contagem ou 1UN. Conteúdo G/ML do arquivo também é ignorado com alerta; número do arquivo > 1000 UN é ignorado com alerta.
- ESCOVA PARA CABELO ganhou os tipos de escova (raquete, redonda, térmica…) e PALETA BOVINA exclui ESCOVA/CABELO (libPatch escova-cabelo-2026-09b).

## Farmácia: agente próprio

- A partir de 2026-09-25 a Farmácia é tratada por um agente separado (pacote em `farma_pacote/` / `farma_pacote.zip`). Neste fluxo o app continua com a lógica de Farmácia como está, mas **não se mexe mais nela aqui**; mudanças de Farmácia vêm do outro agente.

## Testes de Farmácia (automáticos)

- `NODE_PATH=$(npm root -g) node testes_farma/rodar.js` abre o `classificador.html` com Playwright, ativa todas as
  categorias, roda os CSVs de `farma_pacote/testes/` e imprime categoria (nome oficial), descritivo, marca, fabricante e
  alertas. Saída atual em `testes_farma/resultados.txt` (comparar com `diff` depois de mexer no código).
- Forma farmacêutica colada no número (`20CP`, `14CP`, `30CAPS`) agora entra no descritivo
  (`PARACETAMOL 750MG 20CP` → `PARACETAMOL COMPRIMIDO 20UN`; antes saía `PARACETAMOL 20UN`).

## Farmácia: marca, dosagem e forma no descritivo (decidido com o cliente)

- Marca = nome comercial; genérico = princípio ativo (LOSARTANA), fabricante = laboratório. `farmaNaoMarca()` descarta
  laboratório, GENERICO, sal/forma e nome com princípio ativo; `nomeComercial()` pega a 1ª palavra da descrição
  (DORFLEX, NEOSALDINA) quando não há marca comercial nas bases.
- Descritivo: marca + complemento + dosagem (`dosagem()`: 500MG, 0.5%, 250MG/5ML, 875MG+125MG) + quantidade na forma
  (`formaUn()`: 10CPRS / 28CAPS / 30DRGS). Laboratório sai do descritivo. A coluna de conteúdo continua em UN.
- CORTICOIDES = `S01B CORTICOIDES` (`FIXOS` em `nomes_oficiais.py`). Laboratórios do grupo continuam pelo grupo.
- Detalhes e pendências em `farma_pacote/LEIA-ME_FARMACIA.md`.

## Farmácia: base de marcas do cliente (Hoja) e ordem DIMA > base do cliente > dicionário

- `dados/farma_marcas/*.tsv` → `python3 farma_marcas.py` → `farmaMarcas` / `farmaCodLab` (ver LEIA-ME 3.5b).
  Ordem de scripts: `farma_pa.py`, `nomes_oficiais.py`, `farma_marcas.py`, `build.py`.
- `compileFM`/`matchFM`: marca comercial → categoria (antes do princípio ativo). No `runAll` (Farmácia): marca na DIMA,
  depois `farmaMarcas`, depois dicionário, depois `nomeComercial`, depois princípio ativo. `palavrasPA` impede que parte
  do princípio ativo (HIDROXIDO de HIDROXIDO DE ALUMINIO) vire marca.
- Teste: `node testes_farma/rodar_hoja.js`.

## Links

- Agente de Farmácia (esta branch): https://claude.ai/artifact/FBP4i6ZktAFc1ymeYWmyP7 — publicar sempre o `farmacia.html`.
- Classificador geral: https://claude.ai/artifact/UFuhJCnyT5Lwi3wYZVMVu1 — não publicar esta branch nele (voltou à
  versão da branch `claude/modest-maxwell-y0utos`).
- DIMA com código do laboratório na marca (`DORFLEX (OPE)`): `dima.py` cria o nome sem código (categorias ATC, sem
  princípio ativo); `nomeComercial` busca o fabricante na DIMA e depois no dicionário (DORFLEX → OPELLA).
