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

## Descritivo com no máximo 60 caracteres

- `DESC_MAX = 60`. Início (tipo/categoria), marca e conteúdo são **obrigatórios** e nunca são cortados.
- Só o complemento (o que fica entre a marca e o conteúdo) se ajusta, nesta ordem: (1) abrevia palavras pela tabela `ABREV` (SORTIDO→SORT, PLASTICO→PLAST, AUTOMATICA→AUTOM, BLISTER→BLIS, POLIETILENO→POLIET, BIVOLT→BIV, PRETO→PTO…), da última para a primeira, só até caber; (2) se ainda passar, tira palavras do fim do complemento (alerta "Descritivo encurtado…"); (3) se só o obrigatório já passar, abrevia o início pela mesma tabela e, se nem assim couber, mantém tudo e alerta "revisar".
- Testes: papelaria 38 e material 9 descritivos ficaram mais completos que no corte simples; nenhum passa de 60; categoria, marca, fabricante e conteúdo sem mudança; Farmácia idêntica a `farma_pacote/testes/resultados_esperados.txt`.

## Opção "Sempre usar os dados do arquivo"

- Checkbox `#sempreArq` (`cfg.sempreArquivo`), liga junto o "Priorizar os dados do arquivo". Categoria, marca, fabricante e conteúdo do arquivo são mantidos mesmo fora do comum; o app só avisa com "Arquivo (mantido): …" (categoria que não bate, marca que não aparece na descrição, fabricante que não é da marca na base, conteúdo muito diferente/objeto com peso/número > 1000) e completa apenas o que vier vazio. O descritivo continua sempre padronizado.

## Modo "Só padronizar o descritivo"

- Checkbox `#soDesc` (`cfg.soDescritivo`). Roda duas passadas (`runCore`): 1ª sem prioridade do arquivo = sugestão pura do app; 2ª com "sempre usar o arquivo" = descritivo padronizado com os dados do arquivo.
- Planilha1: categoria, marca, fabricante e conteúdo exatamente como vieram no arquivo (vazio no arquivo → o do app) + coluna `STATUS SUGESTAO` ("ARQUIVO CONFIRMADO" / "SUGESTÃO DIFERENTE: marca, …" / "| ARQUIVO VAZIO: …").
- Aba `SUGESTAO`: só os itens em que o app sugere diferente (arquivo x sugestão lado a lado). RESUMO conta os status.
- RESUMO e tela também mostram "MARCA x ARQUIVO": por que a marca ficou diferente da do arquivo (arquivo sem marca, arquivo com OUTRA MARCA, marca não aparece na descrição…).
- Correção: marca do arquivo escrita de outro jeito (abreviação da mesma marca na base) não é mais trocada.

## Categoria coerente -> mantém tudo do arquivo (2026-09-30)

- `arqOk` (runCore): prioridade do arquivo ligada, categoria do arquivo existe e foi mantida (bate com a descrição) e não é Farmácia → `manter` = mesmo comportamento do "sempre usar": marca, fabricante e conteúdo do arquivo ficam, só com aviso "Arquivo (mantido): …". OUTRA MARCA do arquivo também fica. Só quando a categoria não bate (outra cesta, `arqTrocada`) o app ajusta tudo.
- Modo só descritivo: 2ª passada agora é o "Priorizar" normal; itens com categoria errada (`catErrada`) saem com os valores do app e status "AJUSTADO PELO APP…"; os demais, exatamente como no arquivo.
- Cores nunca são marca (`MARCA_NAO`: MARINHO, AZUL, TURQUESA, NEON, LILAS, AZUL MARINHO…).

## Ajustes de 2026-10-06 (backlog Scanntech com colunas *_sugerida)

- Colunas: `*_sugerida` têm prioridade sobre o cadastro atual; subcategoria vale no lugar da categoria quando preenchida; POR DEFECTO / SIN FABRICANTE ASOCIADO / 0 viram vazio (`limpaArq`). Conteúdo Scanntech: `quantity_sugerida` (total em g/ml/un) + `measurement_sugerido` + `unit_content_sugerido` (`qtdColunas`). ANALISTA é repassado para Planilha1/SUGESTAO.
- Quantidade: arquivo com 1 (UN) é tratado como padrão; se a descrição tem peso/volume ou contagem (C/10, 10UN), vale a da descrição (alerta "Arquivo com 1UN…", `qDesc`). Calçado (chinelo, sandália, babuche, tênis…) é vendido por unidade: número da descrição é tamanho.
- CARAMELO MASTIGAVEL: descritivo começa com BALA + tipo (`BALA_TIPOS`: GOMA, GELATINA, LIQUIDA, MARSHMALLOW, ALCACUZ, RECHEADA, DURA, MASTIGAVEL); com BALA na descrição e sem tipo → BALA MASTIGAVEL; sem cara de bala, regra antiga.
- OUTRA MARCA: colunas POSSIVEL MARCA / ORIGEM (`possiveisMarcas`): marca da base do app (passada de sugestão) ou a 1ª palavra da descrição que não é tipo/abreviação de tipo, sabor/cor (aparece em ≥6 categorias), medida ou número — "CONFERIR".
- Modo só descritivo: categoria nunca é trocada (aviso POSSÍVEL CATEGORIA ERRADA + CATEGORIA SUGERIDA APP).
- `rodar.js`: roda o app em Chromium headless para backlogs grandes (200 mil+).
- DUN-14: código de barras com 14 dígitos é tratado como caixa (`packCaixa`): pack NxQ na descrição, ou CX/FD/DP/PCT/C/ + número de unidades combinado com o conteúdo da unidade (ex.: "350ML FD C/12" → 12X350ML). Sem pack na descrição: alerta "Código de 14 dígitos (caixa) sem quantidade de unidades na descrição; revisar".
- BALA PASTILHA só com indicação clara (PASTILHA, PASTILHAS, DROPS, BALA DURA); BALA/BALAS/BALINHA/JUJUBA/BALA DE GOMA… vão para CARAMELO MASTIGAVEL (libPatch `bala-pastilha-2026-10`).
- MIX NUTS não pega mais "MIX" solto (só MIX NUTS, MIX DE CASTANHAS, TRAIL MIX, NUTS…) e exclui BALA/GOMA/CANDY/CHEWY/GUMMY; CARAMELO MASTIGAVEL reconhece CANDY, CHEWY, GULOSEIMA (libPatch `mix-nuts-bala-2026-10`). Tipo da bala (BALA GOMA…) procurado em todas as descrições do código.
- CONFEITO sozinho vai para CARAMELO MASTIGAVEL (BALA MASTIGAVEL…); CHOCOLATE CONFEITO só com indicação de chocolate (CONFEITO DE CHOCOLATE, CONFETI, DISQUETI, M&M, CONFEITO MM, DRAGEADO…); CONFEITARIA OUTROS não pega mais CONFEITO solto (libPatch `confeito-2026-10`). Atenção: "MM" sozinho é milímetro, nunca usar como termo.
- Ao carregar o backlog, categorias que o arquivo traz e estão desligadas são ativadas automaticamente (aviso no status do backlog).
- DUN-14: também reconhece o número antes da embalagem ("36PCTX", "12 CX", "24 PACOTES") via `RX_NCX` → ex.: 36PCTX + 190G = 36X190G.
- `aggregate`: descrições divididas entre categoria de objeto (cesta BAZAR/TEXTIL/ELETRO/CONSTRUCAO) ou nada e uma categoria de consumo, num produto com peso/volume (G/ML) → vence a de consumo (flag CONSUMO_VENCE). Ex.: "FINI OCULOS HARRY POTTER 70G" + "BALA DE GELATINA FINI 70G" → CARAMELO MASTIGAVEL.
- `balaTipo`: tipo escrito logo depois de BALA ("BALA DE GELATINA") tem prioridade sobre a ordem da lista.
- Balas x sabor x marshmallow (libPatch `balas-sabor-2026-10` + `aggregate`): as 29 categorias de fruta in natura (`FRUTAS`) excluem palavras de doce (BALA, GOMA, DROPS, PIRULITO, MARSHMALLOW, GELATINA, CANDY, SABOR…); fruta em pack (NxQ) vira OUTRA CATEGORIA. Na votação, se alguma descrição aponta `DOCES_CAT` (CARAMELO MASTIGAVEL, BALA PASTILHA, PIRULITO, DOCE OUTROS, GOMA DE MASCAR) e o resultado é OUT/fruta/`CONFUNDE_DOCE` (DOCINHO, GELATINA, AROMA E ESSENCIA, CARNES PREP CONGELADAS, CAFE SOLUVEL, CAPPUCCINO, LEITE COMUM, CHOCOLATE BOMBOM, GRELHA E ESPETO), vence o doce (flag DOCE_VENCE).
- (substituído em out/2026, ver abaixo) Marshmallow ia para DOCE OUTROS. BALA DE COCO → CARAMELO MASTIGAVEL ("BALA COCO…"), RAHAT/GOMA ARABE/GOMA FINI → CARAMELO; PIR/PIRUL/CHUPETITA → PIRULITO.
- `coerentes`: se a 1ª descrição não combina com quase nenhuma e outra combina com a maioria, a referência passa a ser essa (ex.: "BISC PASSATEMPO" no meio de 9 descrições de bala).
- Cestas: `K.cestas` (planilha CATEGORIA x CESTA de 2026-10 + cesta da biblioteca para quem não está na planilha). `migrarCategorias` só preenche categoria **sem cesta**; cesta existente nunca é trocada. As 40 categorias do trabalho padrão (cfg) ganharam cesta.
- EST MER 6 por categoria: `K.segPadrao` atualizado pela planilha CATEGORIA x SUBCATEGORIA (categoria DIMA → categorias do app; 616 categorias, farmácia fora). `segmentosEstMer6` usa a da planilha **somada** à aprendida das marcas do backlog. Ex.: CARAMELO MASTIGAVEL, BALA PASTILHA, PIRULITO → BALA E PIRULITO (FINI passou a ser reconhecida).
- Nunca pôr nome de marca em "incluir" de categoria (vira vocabulário da categoria e a marca deixa de ser reconhecida) — foi o caso de GOMA FINI.
- OUTRA MARCA / OUTRO FABRICANTE do arquivo não travam mais: se a descrição traz marca da EST MER 6, vale ela (também no modo só descritivo).
- CARAMELO MASTIGAVEL com marca reconhecida e sem a palavra BALA: descritivo BALA MASTIGAVEL….
- Descritivo sem palavra repetida (`mesmaPalavra`): plural ou grafia próxima da mesma palavra (MARSHMALLOW/MARSHMELOWS, CADEADO/CADEADOS, CALCULADORA/CALCULATOR) entra uma vez; palavras ≤3 letras podem repetir; em palavras <8 letras só o plural conta. Conector solto no fim do complemento é retirado.
- Repetição no descritivo é checada palavra por palavra também dentro de expressões do complemento (LEITE_DE_COCO); conector só fica se as palavras dos dois lados ficarem (ou se se liga ao início).
- Planilha1: colunas UNIDADES e CONTENIDO UNITARIO antes do CONTENIDO (pack 12X100G → 12 | 100 | 1200; unitário 100G → 1 | 100 | 100), a partir de q.n / q.uv (`qn`, `quv` no resultado).
- Planilha1: coluna EST.MER. depois de CATEGORIA (`estMerOf`, tabela `K.estMer` da planilha CATEGORIA x EST MER; busca pelo nome que sai na planilha, nome interno, sem código ATC ou nome oficial). Nome duplicado na planilha com códigos diferentes (ATUM, COLAGENO, CHUPETA, MAMADEIRA, LEAVE IN, ANTIBIOTICO, VACINA…) sai em branco.
- MAIONESE reconhece MAION/MAIONES/MAYONNAISE/MAYONESA (libPatch `maionese-2026-10`). Descritivo também não repete abreviação (4+ letras, terminando em consoante) de palavra já usada: MAIONESE MAION → MAIONESE; BARBANTE BARB; CONJUNTO CONJ.
- PAPINHA: reconhece PURE DE FRUTAS, SOPINHA, PAPIN, ALIMENTO INF, ZZPAP; exclusão de PURE só para PURE DE BATATA/TOMATE/INSTANTANEO; frutas excluem PURE/PAPINHA/SOPINHA/POUCH; se alguma descrição vota PAPINHA, vence PAPINHA (libPatch `papinha-2026-10`).
- Marca considerando a DIMA: busca primeiro na categoria DIMA da planilha (`seg`), a aprendida (`seg.extra`) só se ali não houver marca ou só houver abreviação; marca curta/genérica (PIC ME) e de 2+ palavras com cara de expressão (DA VOVO) valem se a DIMA as registra na categoria do item (a de expressão só como último recurso); abreviação cadastrada (COLOR→COLORADO, DOUR→DOURO, IMP→IMPERIO) pesa 0,6.
- Pó de cacau/chocolate (libPatch `cacau-po-2026-10`): CACAU EM PO reconhece CACAU PO/CACAU 100; CHOCOLATE EM PO OUTROS reconhece CHOC PO/CHOCOLATE PO/SOLUVEL (e exclui CACAU 100); ACHOCOLATADO EM PO reconhece ACHOC PO; todas as CHOCOLATE * (tablete, bombom, saudável…) excluem PO/EM PO/SOLUVEL/ACHOC*. CHOCOLATE EM PO OUTROS ganhou início fixo "CHOCOLATE EM PO" (`K.inicioPatch`, só preenche categoria sem início).
- Pipoca micro-ondas: MANTEIGA e BACON excluem PIPOCA/POPCORN/MICRO/MICROONDAS/SABOR (libPatch `pipoca-2026-10`). Descritivo fica "PIPOCA MICRO…" e MICROONDAS/MICRO ONDAS sai do complemento (REMOVER_PATCH em `migrarCategorias` → `c.remover`).
- `K.marcasNaLista` (MARCAS_NA_LISTA): nomes de marca que estão na lista "incluir" de categorias (PRINGLES, LAYS, RUFFLES, STAX, DORITOS, CHEETOS em BATATA/salgadinho; KIT KAT, TWIX, BIS, SONHO DE VALSA… nos chocolates; NESCAFE) ajudam a achar a categoria mas não viram vocabulário nem "tipo do produto": continuam sendo reconhecidos como marca. Ao pôr marca em "incluir", acrescentar também nesta lista.
- Exceção: balas de gengibre, mel e própolis → BALA PASTILHA (BALA DE GENGIBRE, BALA GENG, BALA MEL, BALA PROPOLIS, MEL E GENGIBRE…); CARAMELO MASTIGAVEL exclui GENGIBRE/GENG/PROPOLIS/PROP (libPatch `bala-gengibre-2026-10`).
- AZEITONA só para azeitona (libPatch `azeitona-2026-10`): sem "AZEIT" solto (pegava AZEITE) nem "AZ VERDE/AZ PRETA" (AZ = azul em calçado); exclui molho, creme, pimenta, alho, pesto, biscoito, grissini, focaccia, sardinha, atum, azeite/oliva, tempero, queijo, salame, calçados e SABOR.

### Bala dura → BALA PASTILHA (libPatch `bala-dura-2026-10`)
- BALA PASTILHA incluir: BALAS DURAS, BALINHA DURA, BALA DUR, RECHEADA DURA etc.; CARAMELO MASTIGAVEL excluir: DURA, DURAS, BALA DUR.
- `DURA` saiu de BALA_TIPOS (bala dura nunca fica em CARAMELO).
- REMOVER_PATCH de BALA PASTILHA: DURA/DURAS/DUR/BALA/BALAS/BALINHA(S) — o início "BALA PASTILHA" já diz isso (sem duplicar).

### Marshmallow → CARAMELO MASTIGAVEL (libPatch `marshmallow-caramelo-2026-10`)
- Todo marshmallow (todas as grafias, MAXMALLOW, NUAGE; bala ou não) vai para CARAMELO MASTIGAVEL (incluir + forte); DOCE OUTROS perde essas palavras (remover_incluir, excluir, remover_forte).
- libPatches agora aceitam `forte` / `remover_forte`.
- Descritivo: `MARSHMALLOW + MARCA + demais informações` (`RX_MARSH` em `balaTipo`, testado antes dos tipos de bala; se o arquivo mantiver DOCE OUTROS no modo só descritivo, o início também é MARSHMALLOW). BALA/BALAS/BALINHA saem do complemento.
- Complemento: palavra retirada leva junto o conector logo depois (BALA DE COCO → "DECARLI RECHEADA", não "DECARLI DE RECHEADA"); só na descrição escolhida, a escolha da descrição não muda.

### Personagem/licença não é marca (`K.personagens`, `PERSONAGENS`)
- Lista em consts.json (`personagens`): MARVEL, DISNEY, THOR, PANTERA NEGRA, WOLVERINE, TURMA DA MONICA, PATRULHA CANINA, STAR WARS…
- `findBrand`: se há personagem entre as candidatas e a categoria é conhecida (EST MER 6), vale primeiro a outra marca registrada na categoria (ZEEDOG, TILIBRA, MOLIN, CIRANDA CULTURAL); sem outra, fica como antes (personagem). Sem categoria conhecida não troca (FUN/AMIGOS seriam escolhidas).
- Pedaço de personagem (HELLO de HELLO KITTY, MONICA, PATROL) nunca é marca.
- `autoSegments` ignora marcas do arquivo que são personagem (elas puxavam o segmento da categoria para ARROZ/BRINQUEDO…).
- Arquivo com marca = personagem e outra marca na descrição: usa a da descrição, inclusive no modo só descritivo (`persArq`, alerta).
- COLEIRA E GUIA PET: PEIT/PEITORAL (libPatch `coleira-peitoral-2026-10`, exclui FRANGO/PERU/CARNE…).
- `qtdColunas`: medida KG/L com valor ≤ 60 vira G/ML ×1000 (15 KG → 15000G); valores maiores já estão em gramas (padrão da base).

### Acessório PET com PET no descritivo + tamanho
- `PET_ACESSORIO` (COLEIRA E GUIA PET, CASA E CAMA PET, ACESSORIO PET OUTROS, ACESSORIO HIGIENE PET, ACESSORIO ALIMENTO PET, HIGIENE E LIMPEZA PET OUTROS): início = tipo por extenso (`PET_TIPO_EXT`: PEIT→PEITORAL, COMED→COMEDOURO…) + PET. Ex.: PEIT.ZEEDOG H NEOPRO MATCHA G → PEITORAL PET ZEE DOG NEOPRO MATCHA TAM G 1UN.
- Tamanho solto (P, M, G, GG, XG…, sem número antes) nessas categorias e em VESTUARIO PET vira "TAM G".
- CHA SOLUVEL / CHA CAPSULA excluem PEIT, COLEIRA, ZEEDOG, NEOPRO, CAO, GATO… (MATCHA é cor) — libPatch `matcha-pet-2026-10`.
- Início igual à marca colada (ZEEDOG = ZEE DOG, STAROFFICE = STAR OFFICE) sai, para não repetir.

### Creme de amendoim, cappuccino, ovo de páscoa, barra de proteína
- CREME DE AMENDOIM: início estava cadastrado como CHOCOLATE COBERTURA → CREME DE AMENDOIM (libSeed + `INICIO_FIX` em migrarCategorias para bibliotecas já salvas); remover CREME/PASTA/MANTEIGA/AMENDOIM/CR; incluir CREME AMENDOIM, PASTA AMENDOIM…; chocolates e amendoins excluem esses termos.
- CAPPUCCINO (todas as grafias) forte em CAPPUCCINO; todas as categorias CAFE * excluem (inclusive CAFE CAPSULA).
- OVO DE PASCOA: incluir/forte OVO PASC, OVO DE CHOCOLATE, OVO KINDER, KINDER SURPRESA…; não exclui mais BRANCO/VERMELHO (chocolate branco); exclui EMBALAGEM/FORMA/MOLDE…; segPadrao OVO DE PASCOA + CHOCOLATE (KINDER só está em CHOCOLATE na DIMA). Chocolates excluem OVO/PASCOA; ovos de galinha excluem KINDER, SURPRESA, LACTA, GAROTO…
- KINDER em `marcasNaLista`; `catVocab` agora ignora palavra de marca da lista também dentro de expressão (OVO KINDER).
- Barra de proteína → CEREAL EM BARRA PROTEICO (sai de SUPLEMENTO OUTROS e demais suplementos); remover PROTEINA/PROTEICA/PROTEIN/BAR/BARRA/BARRINHA no descritivo. libPatches `capuccino-ovo-amendoim-2026-10`, `barra-proteina-2026-10`.

### Embalagem para ovo de páscoa / doces → EMBALAGEM ALIMENTO
- `aggregate`: 1ª descrição com EMBALAGEM/EMBALAGENS/EMBALAGEN (ou EMB como 1ª palavra) + OVO/PASCOA/TRUFA/BOMBOM/BRIGADEIRO/DOCE/CHOCOLATE → EMBALAGEM ALIMENTO (flag EMBALAGEM_OVO), antes das outras regras. "OVOS BRANCOS EMB C/12" continua ovo.
- libPatch `embalagem-ovo-2026-10`: EMBALAGEM ALIMENTO incluir/forte EMBALAGEM OVO DE PASCOA, SACO OVO DE PASCOA…; chocolates e OVO DE PASCOA excluem EMBALAGEM/CELOFANE/CROMUS; EMBALAGEM OUTROS exclui OVO/PASCOA.

### Massa para sopa → MASSA TRADICIONAL (libPatch `massa-sopa-2026-10`)
- SOPA E CREME exclui MASSA/MASSAS e MASSA (PARA) SOPA, MACARRAO (PARA) SOPA (mas não MACARRAO solto: "SOPA INSTANTANEA COM MACARRAO VONO" segue sopa).
- MASSA TRADICIONAL incluir/forte essas expressões + GUELA. Formatos soltos (AVE MARIA, ESTRELINHA, LETRINHA) não entram: são ambíguos (bíblia, decoração, SOPA LETRINHA).
- PHRASE protege "AVE MARIA" (TOK expandia AVE → AVELA): BIBLIA AVE MARIA e massa AVE MARIA não viram "AVELA MARIA".

### Pipoca: sabor nunca é a categoria (`aggregate`, flag PIPOCA_VENCE)
- 1ª descrição com PIPOCA + MICRO/MICROONDAS/MICRO-ONDAS/MICROOND → PIPOCA MICRO-ONDAS (CALABRESA, PICANHA, QUEIJO, CHOCOLATE, LEITE CONDENSADO, PRESUNTO, PIZZA… não puxam mais para linguiça, carne, queijo, biscoito…).
- Começa com PIPOCA e a votação caiu em outro alimento → categoria de pipoca votada ou PIPOCA PRONTA.
- Não vale para PIPOQUEIRA, PANELA, MAQUINA, BALDE, SACO, EMBALAGEM.

### Pipoca (2ª rodada) + regra ensinada vence a categoria do arquivo
- `pipocaCat`: PIPOCA / POPCORN / POP CORN em qualquer posição; + MICRO… → PIPOCA MICRO-ONDAS; MILHO + MICRO (sem VERDE/LATA/CONSERVA/CANJICA…) → PIPOCA MICRO-ONDAS ("DOCE MILHO MICRO"); sem MICRO e caiu em outro alimento → PIPOCA PRONTA; sem categoria só com peso (G). Bloqueia PIPOQUEIRA, CARTUCHO, SAQUINHO, CAIXA, EMBALAGEM, BRINQUEDO…
- `REGRA_FORTE` (PIPOCA_VENCE, EMBALAGEM_OVO, PAPINHA_VENCE, DOCE_VENCE) em `categoriaArquivo`: no modo priorizar arquivo a categoria do app vence a do arquivo (QUEIJO OUTROS / BACON em pipoca); no modo só descritivo continua a do arquivo com POSSÍVEL CATEGORIA ERRADA + CATEGORIA SUGERIDA APP.
- (atualização) Também no modo só descritivo a `REGRA_FORTE` troca a categoria do arquivo (`regraForte`): exportação usa a categoria do app, EST.MER. dela, e STATUS = "CATEGORIA TROCADA PELA REGRA (ARQUIVO: <categoria do arquivo>)". Pedido do usuário depois de KANTY/TORDILHO PIPOCA MICRO QUEIJO saírem em QUEIJO OUTROS.

### Pipoca (3ª rodada) + base de regressão dos exemplos ensinados
- `pipocaCat` olha TODAS as descrições do item (SINHA CHOCOLATE 100G + PIPOCA MICRO SINHA…): micro-ondas em qualquer uma vence; aceita PIP/PIPOC e MIC, M ONDAS, MO.
- POP / CORN de "POP CORN" nunca é marca. REMOVER PIPOCA MICRO-ONDAS ganhou MIC, PIP, PIPOC, POPCORN, MO.
- `testes/regras_ensinadas.csv` (111 exemplos que o usuário ensinou, com categoria e marca esperadas; marca * = não confere) e `testes/testar_regras.js`. **Rodar antes de publicar**: `NODE_PATH=/opt/node22/lib/node_modules node testes/testar_regras.js classificador.html <xlsx.full.min.js>` — deve dar 111 de 111. Todo exemplo novo que o usuário mandar entra nesse arquivo.

### Vinagre de álcool não é ALCOOL LIMPEZA (libPatch `vinagre-alcool-2026-10`)
- ALCOOL LIMPEZA, ALCOOL ANTISSEPTICO e MISTURA ALCOOLICA OUTROS excluem VINAGRE/VINAG.
- VINAGRE ALCOOL: incluir VINAGRE (padrão sem tipo), VINAGRE ALC, VINAGRE BCO, VINAG…; remover ALC/VINAG no descritivo. Balsâmico, fruta, cereal, vinho, mel seguem nas suas categorias.
- 14 exemplos adicionados em `testes/regras_ensinadas.csv` (125 no total).

### Atum / salada de atum / chicharro (libPatch `atum-salada-2026-10`) + abreviações de marca
- Categorias de ingrediente (BATATA*, LEGUMES, MIX DE LEGUMES, ERVILHA/MILHO/SELETA EM CONSERVA, AZEITONA, PETISCO OUTROS…), todas as QUEIJO*, SHAMPOO* e MOLHO* excluem ATUM/SARDINHA/CHICHARRO/CAVALINHA (QUEIJO e SHAMPOO também PEIXE). "SNACK SALADA ATUM … BAT", "QUEIJO RALADO ATUM", "SH ATUM SOLIDO" → ATUM.
- ATUM incluir SALADA DE ATUM, ATUM RALADO, ATUM SOLIDO, CHICHARRO (pedido do usuário: chicharro ralado entra em ATUM). SARDINHA incluir SALADA DE SARDINHA.
- `marcaAlias` (consts) = abreviações de marca ensinadas: GOMES COSTA, DA COSTA, G DA COSTA, GOMES → GOMES DA COSTA. Entra no mapa da DIMA (como as abreviações da DIMA) e `comAlias` reescreve a descrição antes de `findBrand` (DA COSTA sozinho era rejeitado por começar com conector). A marca continua precisando estar registrada na categoria do item.
- +21 exemplos em `testes/regras_ensinadas.csv` (146 no total).

### Peixe em conserva vence ingrediente/tempero (`peixeCat`, flag PEIXE_VENCE, em REGRA_FORTE)
- Qualquer descrição do item com ATUM/CHICHARRO → ATUM; SARDINHA → SARDINHA (ou SARDINHA ENLATADA). ALHO, MANJERICAO/PESTO, BATATA, QUEIJO, ERVILHA… nunca ganham ("ALHO FILE DE ATUM GOMES DA COSTA", "ATUM … PESTO MANJERICAO" → ATUM).
- Não vale com RACAO/SACHE/GATO/CAO/PET/WHISKAS/FRISKIES…, ISCA/PESCA, PIZZA/TORTA/SALGADO/EMPADA/PASTEL/SUSHI… (RX_PEIXE_NAO); ATUM/SARDINHA também excluem essas palavras.
- PEIXE_VENCE é marcado mesmo quando a votação já deu ATUM, para vencer a categoria do arquivo (ALHO, ERVA FRESCA) nos modos priorizar e só descritivo.
- +9 exemplos em `testes/regras_ensinadas.csv` (155).

### Essência de narguilé → OTP - OUTROS TABACO (`essenciaOTP`, flag ESSENCIA_OTP, em REGRA_FORTE)
- ESSENCIA/ESS + (palavra de narguilé: NARGUILE, HOOKAH, SHISHA, ROSH, TABACCO… OU marca que a DIMA registra no segmento "OTP OUTROS TABACO": IGNITE, ZOMO, ADALYA, ONIX TABACCO, ESSENCIA FULL…). Marca também de confeitaria/aroma/vela (NAY) só vai para OTP se tiver gramatura em G.
- Nunca: AMBIENTE, DIFUSOR, VARETAS, VELA, AROMATIZADOR, CULINARIA, CONFEITARIA, LIMPEZA, PERFUME, OLEO ESSENCIAL… (RX_ESS_NAO). Essência culinária (FLEISCHMANN, MAGO) segue AROMA E ESSENCIA.
- Descritivo: ESSENCIA + MARCA + complemento + gramatura (ini fixo "ESSENCIA"; REMOVER OTP: ESS, ESSENC). Quantidade: com G sai a gramatura; sem, 1UN.
- Limitação: número solto no nome do sabor ("LOVE 66") sai do descritivo (cleanTokens tira palavras com dígito).
- +14 exemplos em `testes/regras_ensinadas.csv` (169).
- (atualização) `marcasOTP` (consts): marcas de OTP mesmo com segmento errado na DIMA — NAY (cadastrada em CONFEITARIA por engano, segundo o usuário). ESSENCIA + NAY → OTP sempre, com ou sem gramatura. +4 exemplos (173).

### Chocolate em pó / achocolatado / cacau em pó (`chocPoCat`, flag CHOCPO_VENCE, em REGRA_FORTE)
- Qualquer descrição do item: ACHOC… → ACHOCOLATADO EM PO; CHOC… + PO/EM PO/SOLUVEL (em qualquer posição: "CHOCOLATE CHOCOLATTO EM PO", "PO CHOCOLATE 50%", "CHOC.PO SOL.") → CHOCOLATE EM PO OUTROS; CACAU + PO → CACAU EM PO. Vence CHOCOLATE OUTROS e a categoria do arquivo.
- Não vale com LIQUIDO, BEBIDA, LACTEA, ML, MISTURA/BOLO, BISCOITO, CEREAL, BARRA, TABLETE, BOMBOM, WAFER, SORVETE, MOUSSE, PUDIM, CAPPUCCINO, CAFE, WHEY, GRANULADO, COBERTURA, RECHEIO, CREME (RX_CHOCPO_NAO).
- REMOVER CHOCOLATE EM PO OUTROS: SOL.
- PEIXE OUTROS tinha PIRACANJUBA (peixe) no incluir e pegava laticínio Piracanjuba: agora exclui LEITE, BEBIDA, LACTEA, CREME, QUEIJO, UHT, ML… (libPatch `chocolate-po-2026-10`); PIRACANJUBA em `marcasNaLista`.
- +23 exemplos em `testes/regras_ensinadas.csv` (196).

### Azeitona (2ª rodada) + linguiça (libPatch `azeitona2-2026-10`)
- Rodado o ARQ1 (105 mil itens do usuário): AZEITONA pegava linguiça com azeitona, guardanapo estampado e calçado com cor AZ/VD.
- AZEITONA exclui outro produto (LING, LINGUICA, PERNIL, CARNE, PAO, PIZZA, GUARD, GUARDANAPO, DECOR, PAPEL, PRATO…), "C/ AZEITONA", "SABOR AZEITONA", PATE/PASTA, e calçado/cores (CHIN, SAND, BABUCH, IPA, CARTAGO, CZ, AZUL, BB, BABY…). Volta a aceitar AZ VDE, AZ PTA, AZ VD, GORDAL (com essas exclusões); RECHEADA continua azeitona.
- PIMENTAO exclui AZEITONA (azeitona recheada com pimentão).
- LINGUICA FRESCA aceita LINGUICA/LING genérico (≈490 linguiças saíram de PERNIL, BACON, QUEIJO, OUTRA CATEGORIA…), excluindo DEF/DEFUMADA, COLONIAL, CALABRESA, prato/salgado/molho, BISC LINGUA GATO, TRIPA, POSTA DE LING (peixe), OCULOS…
- LINGUICA DEFUMADA aceita DEF, DEFUM, COLONIAL, BLUMENAU, PARMA; REMOVER DEF/DEFUM. PERNIL e ERVA CHA excluem LING/LINGUICA. SALSICHA/LINGUICA VEGETAL exclui ARTESANAL, PERNIL, TRADICIONAL, CARNE.
- +18 exemplos em `testes/regras_ensinadas.csv` (214).

### Doce de leite, doce em barra, leite condensado, shampoo (`doceCat`, flag DOCE_REGRA em REGRA_FORTE; libPatch `doce-leite-shampoo-2026-10`)
- D LEITE / D.LEITE / DOCE (DE) LEITE em qualquer descrição → DOCE DE LEITE (nunca LEITE COMUM); DOCE + BARRA/TABLETE/CORTE → DOCE BARRA (goiabada/amendoim/paçoca seguem as suas). Não vale com biscoito, bolo, sorvete, alfajor, bombom, bala, chocolate, sabão/ERVA DOCE, limpeza… (RX_DOCE_NAO).
- SHAMPOO* / SABONETE EM BARRA / CONDICIONADOR EM BARRA excluem DOCE, GOIABADA, BANANADA, COCADA, CRISTALIZADO…
- BISCOITO LEITE não tem mais LEITE CONDENSADO (ia para lá); LEITE CONDENSADO aceita LEITE COND.
- Modo só descritivo: categoria do arquivo de OUTRA CESTA sem nenhuma palavra dela na descrição (SHAMPOO num doce) também é trocada (regraForte, status CATEGORIA TROCADA PELA REGRA).
- PHRASE "S C" → SEM CAROCO só com AZEITONA/AMEIXA/TAMARA/CEREJA na descrição (aparecia em doce de leite, recibo, forcado…).
- +17 exemplos (231).

### OUTRA CATEGORIA só em último caso (fim de `aggregate`; `tipoCategoria`, `C.inativas`, consts `tipoCategoria`; libPatch `outra-categoria-2026-10`)
- Quando nada bate (r.cat === OUT), em ordem:
  a) tabela de tipos do produto (consts `tipoCategoria`: BISC/BOLACHA/CAVACA… → BISCOITO OUTROS; TEMPERO/TEMP/LEMON/CONDIMENTO/CHIMICHURRI → TEMPERO INDUSTRIALIZADO; MOLHO/MOL → MOLHO OUTROS; SUSPIRO/MERENGUE/COCADA/DOCE → DOCE OUTROS; BANANADA/RAPADURA → DOCE BARRA; PACOCA → PACOCA; GELEIA → GELEIA OUTROS; SAND → SANDALIA; CHIN → CHINELO; CALDO → CALDO), em qualquer descrição — não vale com TINTA, GUACHE, CARTUCHO, EMBALAGEM, LV/LIVRO, CAIXA, FORMA, PORTA… (objeto);
  b) categoria INATIVA da biblioteca (menos farmácia) que bate pelas regras, se a 1ª palavra da descrição for o tipo dela (flag CATEGORIA_INATIVA);
  c) regras ignorando a lista "sempre OUTRA CATEGORIA" (BOMBONA…), com a mesma exigência da 1ª palavra (flag CATEGORIA_DESC);
  d) nome de categoria igual à 1ª palavra (ou "<PALAVRA> OUTROS").
- As regras próprias (pipoca, peixe, essência, chocolate em pó, doce, embalagem de ovo) usam `C.libNames` (biblioteca inteira), então valem mesmo com a categoria desativada.
- Ajustes: SHOYU/SHOYO → MOLHO DE SOJA; MOLHO DE PIMENTA aceita CREME DE PIMENTA, CAROLINA REAPER, HABANERO, SRIRACHA, MALAGUETA, BIQUINHO, SWEET CHILLI… (não PIMENTA solta; exclui PO, GRAO, BISC, SALGAD…); MOSTARDA forte (OUTRAS VERDURAS exclui bisnaga/ML/molho…); LIMAO exclui PEPPER/TEMPERO; TEMPERO INDUSTRIALIZADO aceita LEMON PEPPER, CONDIMENTO, PEGA MARIDO/ESPOSA; MASSA CASEIRA exclui doce/paçoca/biscoito; PACOCA aceita PASSOCA; TORRONE forte em DOCE BARRA; CREME DE LEITE aceita CREME LEITE/CR LEITE; AZEITE DE OLIVA aceita OLIVA/EXT VIR/ARBEQUINA/PICUAL (AZEITONA e AZEITE OUTROS excluem); CARAMELO MASTIGAVEL exclui CALDA/COBERTURA; SOBREMESA* exclui MOLHO/PIMENTA; LEITE CONDENSADO exclui bebida/iogurte/picolé…; doce de leite exclui sorvete/picolé/churros/cuca/iogurte/pão/pasta de amendoim/rapadura.
- ARQ1 (105 mil): OUTRA CATEGORIA 13.745 → 9.290. Papelaria: 2.414 → ~2.230.

### Ovo só quando a descrição diz OVO (libPatch `ovo-generico-2026-10`)
- OVO BRANCO/CAIPIRA/VERMELHO/OUTROS/CODORNA/PASTEURIZADO: `tambem` = OVO, OVOS, GEMA, CLARA (palavra obrigatória) e excluem BISC, BOLACHA, COCADA, DOCE, CHOCOMOLE, MOLHO, PIMENTA, SUSPIRO, SCHMIER, DONUTS, SOBREMESA, PAPA OVO… (libPatches agora aceitam `tambem`).
- `faltaObrigatoria` (só categorias OVO …): categoria do arquivo que exige OVO e nenhuma descrição tem → troca pela do app (mesmo na mesma cesta), nos modos priorizar e só descritivo. Não generalizar: outras categorias da biblioteca têm `tambem` incompleto (IOGURTE LIQUIDO exige IOGURTE e "BEB LACTEA" não tem) — testado: troca indevida de 135 itens.
- tipoCategoria: SCHMIER/CHIMIA → GELEIA OUTROS; SOBREMESA → SOBREMESA PRONTA OUTROS; DONUTS/SONHO → DOCE PADARIA. Palavras genéricas da tabela (DOCE, MOLHO, CALDO, GELEIA, DONUT…) só valem como 1ª palavra (TIPO_SO_INICIO).
- Também: BONECA exclui biscoito/alimento (PAPA OVO BISC … BARBIE); TUBO E CONEXAO exclui SUSPIRO/DOCE (UNIAO SUSPIRO); FRUTOS DO MAR OUTROS exclui COCADA/DOCE (COCADA … VIEIRA); BANANA exclui BANANINHA/BANANADA/DOCE; OUTRAS FRUTAS exclui ESPUMA/DRINK; PAPELARIA OUTROS exclui MOLHO.
- Teste: 30 mil itens do ARQ1 com categoria do arquivo, modo só descritivo: 9 categorias exportadas mudaram (de 30.000).

### Atributo/sabor nunca é a categoria — regra geral (amendoim, ovo, azeitona… e todas as famílias)
- Pedido: "está trazendo muita coisa como AMENDOIM, inclusive MOLHO; se está em ML é impossível ser amendoim; corrija para todas as categorias (já tive com azeitona, ovo, agora amendoim)".
- **Unidade ML** (consts `categoriasSolidas`, `ehSolida`, `itemML`, `semSolidas`): item só em ML/L (sem G) nunca entra em categoria de produto sólido (amendoim, castanha, ovo, azeitona, biscoito, bala, pipoca, arroz, massa, café em grão/moído, carne, queijo…). Vale na votação, nas categorias inativas, na tabela de tipos e, no fim de `aggregate`, também para as regras especiais (pipoca, doce…: flag UNIDADE_ML). No modo arquivo, categoria sólida do arquivo em item ML é trocada.
- **Produto + atributo** (`splitAtributos`, consts `atributos`): nas categorias cujo nome é "PRODUTO + atributo" (AMENDOIM SALGADO/DOCE/NATURAL, OVO BRANCO/VERMELHO/CAIPIRA/PASTEURIZADO, IOGURTE NATURAL, FEIJAO BRANCO/PRETO, VINHO BRANCO, ARROZ JAPONES, BISCOITO RECHEADO), termo da lista que é só atributo (SALGADO, PIMENTA, CEBOLA, SABOR, COM SAL, BRANCO, JAPONES…) só conta com o produto na descrição (AMENDOIM/AMEND/AMEN, OVO, IOG…; qualquer começo da palavra com 3+ letras). Só usa a lista `atributos` para o nome (POLVILHO, BIJU, VEGETAL, "DE PIMENTA" não são atributo).
- **Modo arquivo** (`faltaProduto` em `categoriaArquivo`): categoria "produto + atributo" do arquivo sem o produto na descrição, ou com palavra que ela exclui (RAPADURA … DOCE DE AMENDOIM em AMENDOIM SALGADO) → troca pela do app (regraForte no só descritivo).
- **Tipo vence sabor** (`tipoNoInicio`, flag TIPO_VENCE_SABOR): categoria votada que é só sabor/ingrediente (fruta, CEBOLA, ALHO, MANGA, PACOCA…, SAL COMUM, FARINHA…) perde para o tipo de produto da tabela `tipoCategoria` nas 4 primeiras palavras (BISC, BOLACHA, MOLHO, COOKIE…): "BISC RESENDE PETA CEBOLA" → BISCOITO POLVILHO; "SAL BOLACHA AGUA E ARTE" → BISCOITO OUTROS; "CHILLI BROTHERS MOLHO MANGA" → MOLHO OUTROS.
- **Rapadura** (`doceCat`): RAPADURA como produto → DOCE AMENDOIM se amendoim em ≥1/3 das descrições (S/SEM AMEND não conta), senão DOCE OUTROS (convenção do ARQ1); o sabor (MAMAO, COCO) nunca é a categoria. Tabela: RAPADURA → DOCE OUTROS.
- **Pimentas** (libPatch `pimenta-2026-10`): PIMENTA BIQUINHO/MALAGUETA/DEDO DE MOCA/CUMARI/VERMELHA/CONSERVA → CONSERVA VEGETAL; PIMENTA (DO) REINO/PRETA MOIDA/EM PO → TEMPERO NATURAL/ESPECIARIA; PIMENTA CREME/CREME PIMENTA → MOLHO DE PIMENTA (BIQUINHO/MALAGUETA saíram dele); TEMPERO CASEIRO → TEMPERO LIQUIDO/PASTOSO/TRITURADO.
- Testes: lista do usuário (52 não-amendoins + 5 amendoins): nenhum não-amendoim fica em AMENDOIM nos 3 modos. testar_regras 327/327; material/papelaria/alimentos: só melhorias (raticida saiu de confeito, caixa de descarga saiu de caramelo); 30 mil do ARQ1 modo só descritivo: ~125 mudanças, quase todas correções (SAND/CHINELO que iam para LARANJA, ACAI, CEREJA, DOURADO; TEMPERO que ia para ALHO/SAL COMUM; BISC que ia para BACON/NATA; SUSPIRO que ia para LIMAO; sorvete em L que ia para pipoca/pistache).

### Shampoo (e qualquer categoria) em item que não é dela (`categoriaArquivo` + `libToda`; `tipoNoInicio` estendido; libPatch `shampoo-biblioteca-2026-10`)
- Pedido: "continua classificando itens que não são shampoos em shampoo" (lista de ~77 biscoitos, temperos, molhos, suspiros, SSD… com descritivo "SH …").
- Modo arquivo: quando o app não acha categoria (OUTRA CATEGORIA) e a categoria do arquivo não tem nenhuma evidência na descrição (nem termo da lista nem palavra do nome), a biblioteca inteira (também as desativadas, menos farmácia) decide; se aponta outra cesta → troca (CATEGORIA TROCADA PELA REGRA no só descritivo; trocada no priorizar). Se nada aponta nada → mantém, mas o status avisa POSSÍVEL CATEGORIA ERRADA ("SH 5KG", "BOL SETE CAPAS").
- Descrição que COMEÇA pelo tipo do produto da tabela (BISC, BISCOITOS, BOLACHA, TEMPERO/TEMP, MOLHO…): categoria de outra cesta não vence (BISC MAISENA DE MAIO ≠ MODA PRAIA; BISCOITOS DE NATAL ≠ ACESSORIO DE NATAL; TEMP … FEIJAO ≠ FEIJAO OUTROS; BISC … BOLO ≠ BOLO TRADICIONAL). Não vale para cesta PET/FARMÁCIA, para DOCE genérico, nem com palavra de objeto (TINTA, GUACHE, CAIXA, POTE, EMBALAGEM… = NAO_ALIM_RX).
- Tabela de tipos em item ML: categoria sólida (TEMPERO INDUSTRIALIZADO) cede para a irmã líquida (TEMPERO LIQUIDO/PASTOSO/TRITURADO).
- Patches: SAL COMUM exclui SEM SAL/S SAL/TEMPERO/COLORIFICO; COLORIFICO → TEMPERO NATURAL/ESPECIARIA; TEMPERO LIQ/TEMP LIQ → TEMPERO LIQUIDO (MOLHO OUTROS exclui); MOLHO SALADA → MOLHO PARA SALADA; SQUEEZE exclui MOLHO/MOSTARDA/KETCHUP/MAIONESE; CALDA (TRES LEITES, P BOLO, CHOCOLATE, CARAMELO, SORVETE) → CONFEITARIA OUTROS; SSD/NVME/HD EXTERNO/DISCO RIGIDO → ACESSORIO PERIFERICO.
- Testes: lista do usuário com arquivo = SHAMPOO LIQUIDO/A SECO/EM BARRA: só 2 ficam (com aviso). 30 mil do ARQ1 só descritivo: ~300 mudanças, quase todas sandálias/chinelos que iam para PLANTA E FLOR, CERVEJA, BONECA, CAFE, CARAMELO… e "Temp P Frango" que ia para SHAMPOO. testar_regras 342/342.

### Bazar, utilidades, brinquedos, papelaria (≈150 categorias da lista do usuário; libPatch `bazar-2026-10`; consts `tipoObjeto`)
- Medição no ARQ1 (21 mil itens dessas categorias, todas as categorias ativas): acerto aceitável 38% → ~67% (ARQ1 usa ACESSORIO COZINHA OUTROS como genérico para prato/talher/caneca: o app usar a categoria específica da lista conta como acerto); OUTRA CATEGORIA 4.612 → ~2.000; itens jogados fora do grupo 6.577 → ~3.000.
- `tipoObjeto` (consts): objeto/utensílio como 1ª palavra (FORMA, ESPETO, GRELHA, PANELA/CACAROLA/CAC/FRIGIDEIRA, XICARA/XIC, CANECA, COPO, TACA, JARRA, POTE, BANDEJA, COADOR, RALADOR, TALHER/GARFO/COLHER/FACA, CONCHA/ESPATULA/PEGADOR, TIGELA/CUMBUCA/MARMITA, TRAVESSA/BOLEIRA/FRUTEIRA, PREND/PREGADOR, SABONETEIRA, CARVAO, CHURRASQ, CADEIRA/BANQUETA, COLCHAO, BONECA, CADERNO, CANETA, LAPIS, COLA, MOCHILA, ESTOJO, BALAO, PALHETA/CAPACETE, PNEU, FOGOS/FOGUETE, VELA…):
  a) item sem categoria → categoria do objeto (vale com POTE/CAIXA/FORMA na descrição, que bloqueiam só a tabela de alimentos);
  b) categoria votada de alimento, roupa ou construção (outra cesta) que não conhece a palavra perde para o objeto (FORMA DE BOLO ≠ BOLO, ESPETO DUPLO ≠ CARNES, FORMA GELO ≠ GELO), a não ser que a categoria do objeto exclua algo da descrição (ESPETO MARSHMALLOW).
- Descartável: TALHER/PRATO/COPO com DESC, DESCARTAVEL, PS ou marca de festa (FORFEST, STRAWPLAS, COPOBRAS, PLASTILANIA, TOTALPLAST, PRAFESTA, ULTRAFEST, MASTER/BELLO FEST, FESTCOLOR) → versão descartável.
- Palavras de material/cor que viravam categoria: MATERIAL OUTROS sem MADEIRA solta (madeira serrada, caibro, ripa…); PISO sem CERAMICA solta; PLANTA E FLOR sem ROSA solta; CONJUNTO DE ROUPA e JOGO excluem utensílios; DOCE PADARIA sem BOMBA solta (bomba de chocolate/creme); CARNES PREP sem ESPETO solto (espeto de carne/frango/coração…); GELO, BOLO, MINI BOLO, AIR FRYER, ERVA CHA, CAFE MOIDO, QUEIJO OUTROS, VINHO OUTROS, PRATO PRONTO (marmita), MESA, BOLA, CORTINA, GANCHO E SUPORTE excluem os utensílios correspondentes.
- Vocabulário de mercado (abreviações das descrições reais e termos conhecidos): automotivo (palheta, aditivo/fluido radiador, DOT 3/4, arla, capacete, câmara de ar, bateria Moura/Heliar/Pioneiro, óleos 20W50/5W30…), festa (balão, cortina metalizada, lança confete, festão, topper), natal (fogos, pisca, bola de natal), banheiro (porta escova/sabonete/toalha, kit/jogo banheiro, tapete, desentupidor), cola (cola quente→COLA BASTAO como no ARQ1, cola inst/super, tenaz, contato, durepoxi), papelaria, brinquedos (Lego, Barbie, Hot Wheels, Nerf, slime, massinha, pipa, patinete, triciclo…), descartáveis, embalagens, guardanapo/papel toalha, vela, fósforo, incenso, etc.
- Nova categoria na biblioteca: ACESSORIO MERCHANDISING (display, expositor, wobbler, stopper, testeira, faixa de gôndola, PDV, banner, brinde). VELA, BRINQUEDO e ARTIGO DE DECORACAO da lista não foram criadas (já existem VELA COMUM/AROMATICA, BRINQUEDO OUTROS, DECORACAO OUTROS).
- Cuidados: PAPEL SEDA fica em OTP; SCOTCH sozinho é whisky (FITA SCOTCH é fita); PILAO é marca de café (só PILAO DE ALHO/SOCADOR é utensílio); LA sozinha não é costura (LA BELLE).

### Limpeza pela ORIGEM (`limpezaCat`, flag LIMPEZA_TIPO; libPatch `limpeza-2026-10`)
- Pedido: "faça o mesmo com a cesta LIMPEZA, sempre se embasando na ORIGEM". O tipo do produto no começo da descrição define a categoria de limpeza; a forma vem das palavras e da unidade; fragrância (LAVANDA, PINHO, FLOR, GLICERINA, COCO), marca (OMO, COMFORT) e "SH" nunca viram categoria.
  - LAVA ROUPAS / SABAO / DET PO: LIQ/GEL ou ML → SABAO LIQUIDO; PO → SABAO EM PO; PASTA → SABAO EM PASTA; BARRA/PEDRA/BAR → SABAO EM PEDRA; só G: SABAO → pedra, LAVA ROUPAS → pó; sem forma → SABAO (nova categoria).
  - DET/DETERGENTE/LAVA LOUCA → DETERGENTE LIQUIDO (MAQ/TABLETE → MAQUINA; ROUPA → sabão; DETERGENTE em KG → SABAO EM PO).
  - AMAC/AMACIANTE: CONC → CONCENTRADO, senão DILUIDO.
  - LIMP/LIMPADOR/LIMPA: PERF+CONC ou ESSENCIA → LIMPADOR ESSENCIA; PERF → PERFUMADO; MULTIUSO/M USO → MULTIUSO; VIDRO, PISO, BANHEIRO/BOX, PISCINA, PEDRA/LIMO/BOLOR (PESADA), ALUMINIO/INOX (POLIDOR METAL), FORNO/COIFA (DESENGORDURANTE); sem tipo → LIMPADOR (nova categoria). Não vale com FACIAL, LENTE, CONTATO, BICOS, PNEU, AUTOMOTIVO, TELA…
  - CLORO, ALGICIDA, CLARIFICANTE, FLOCULANTE, BARRILHA, SULFATO DE ALUMINIO, ELEVADOR/REDUTOR DE PH → LIMPADOR PISCINA (como no ARQ1); AGUA SANITARIA/QBOA/CANDIDA/CLORO ATIVO → AGUA SANITARIA.
  - DESINF/DESF, ALVEJ/TIRA MANCHA/VANISH, INSET/RATICIDA/MATA BARATA…, SAPONACEO, ESPONJA (aço/inox → metálica), LA DE ACO/BOMBRIL, LUVA (látex/borracha/multiuso/Sanro/Mucambo → LUVA LIMPEZA; nitrílica/procedimento/térmica/esporte ficam com o app), VASSOURA, RODO, MOP/ESFREGAO, BALDE, PA (de lixo), PANO/FLANELA/PERFEX, SACO LIXO, ESCOVA (sanitária/lavanderia), ROLO ADESIVO, CERA (piso), LUSTRA MOVEIS/PEROBA, GRAXA SAPATO, ODORIZADOR/AROMATIZADOR (roupa → ODORIZADOR DE ROUPA; senão PURIFICADOR DE AR; carro fica automotivo), PASSA FACIL/GOMA, SECANTE, REMOVEDOR, ALCOOL (não gel/mãos), ÁCIDO MURIÁTICO/DESINCRUSTANTE, PEDRA/BLOCO/GEL SANITÁRIO, ANTIMOFO/NAFTALINA, ESSÊNCIA de limpeza.
- Categorias de outras cestas que roubavam itens de limpeza agora excluem os termos (AROMA E ESSENCIA, PISO, LAVADORA DE LOUCA, PISCINA E ACESSORIO, BALA PASTILHA, CONFEITO GRANULADO, TOUCA E LUVA, SHAMPOO LIQUIDO, SABONETE LIQUIDO, MATERIAL OUTROS). INCENSO saiu de PURIFICADOR DE AR (é categoria de bazar).
- Novas categorias na biblioteca: LIMPADOR, AMACIANTE, SABAO (genéricas, só recebem pela regra quando não há tipo/forma).
- Medição no ARQ1 (3.708 itens de limpeza): 42% → ~70%; OUTRA CATEGORIA 553 → ~80. O resto é em boa parte ruído do arquivo (luva de boxe/karatê como LUVA LIMPEZA, detergente de louça como SABAO LIQUIDO).

### Shampoo de novo, papel higiênico, descritivo de sabão (libPatches `shampoo-dima-2026-10`, `papel-higienico-2026-10`)
- "SH …" (arquivo SHAMPOO) em álcool, sabão, inseticida, cabo…: (1) `limpezaCat` também acha o tipo depois da marca (PURA CASA ALCOOL, MIREX … FORMICIDA, AEVA REMOVEDOR; só palavras químicas: SABAO/SABA, ALCOOL, DETERG, AMAC, DESINF, ALVEJANTE, INSETICIDA/FORMICIDA, REMOVEDOR, LIMPADOR, LAVA, CLORO, DESAM…; não vale se a descrição começa por objeto/tipo conhecido: GIZ, CANETA, MARCA TEXTO, SUPORTE…); ROUPA + marca de sabão (YPE, TIXAN, OMO…) com peso = sabão; SABA = SABAO; DESAM/PASSA ROUPA = FACILITADOR.
  (2) `marcaApoia` (DIMA): categoria do arquivo de PERFUMARIA/LIMPEZA (não "OUTROS") sem nenhuma evidência na descrição (termo, palavra do nome ou abreviação dele: MORT, IOG…) e app sem categoria: se TODAS as marcas encontradas no DIMA só têm segmentos de categorias de outra cesta (YPE, PURA CASA: limpeza) → troca para OUTRA CATEGORIA; marca com o segmento (PANTENE: SHAMPOO) ou desconhecida → mantém. Testado em 30 mil itens: trocas só em itens que o arquivo errava ou duvidosos.
- Descritivo: abreviação de palavra do começo (SABAO LIQUIDO … LIQ, SABA; AMACIANTE … AMAC) e plural (LUVA … LUVAS) saem; abreviação de outra palavra já presente sai (LIQUIDO … LIQ, PAPEL … PAP, LIVRO … LIV, PIRULITO … PIR; não vale para palavras comuns/sabores, nem MAN de ONE PUNCH MAN). REMOVER_PATCH: SABAO* sem LAVA/ROUPA(S)/LV/BARRA (pedra); DETERGENTE sem LAVA/LOUCA(S)/DET.
- Papel higiênico: PAPEL HIG, PAP HIG, P HIG, HIGIENICO/HIGIENIC, ROLAO, BIG ROLL, PAPEL INSTITUCIONAL… (não rolete/suporte/jornal pet); PAPELARIA OUTROS, CHOCOLATE e BATATA excluem HIG/HIGIENICO/ROLAO. Descrição só com marca (CONCEITO 1UN, PREZUNIC 12UN) não tem como saber sem a categoria do arquivo.
- Também: lâmina de barbear (BIC, WILKINSON, GILLETTE, LAMINA BARB, SUPER BARBA…; não serra/estilete/roçadeira), acessório de cabelo (xuxinha, rabicó, piranha, presilha, clips p/ cabelo), pomada capilar (pasta/cera modeladora), ativador de cachos, adesivo de citronela → REPELENTE, estabilizador/nobreak/cabo tipo C → CABO/CARREGADOR.

### PERFUMARIA (~200 categorias da lista do usuário; `perfumariaCat`, `infantilDe`, flags PERFUMARIA_TIPO / INFANTIL; libPatch `perfumaria-2026-10`)
- Sem base rotulada de perfumaria (ARQ1 é alimento/bazar): montado conjunto de teste com descrições no padrão do varejo (testes em scratchpad perf/syn 406 + perf/h 82 de controle, não usadas no ajuste). Antes 64% → 98% no ajuste e 100% no controle (82/82). 276 exemplos foram para testes/regras_ensinadas.csv (665 no total).
- `perfumariaCat`: tipo pela 1ª palavra/abreviação do varejo: SH/SHAMP (seco, barra, kit c/ cond), COND/CONDIC (COND só com ML e sem tempero/condimento), KIT SH, CR DENT/CREME DENTAL/GEL DENTAL (sensitive/white/clareador/total 12/gengiva → TRATAMENTO), ESC DENT (elétrica, interdental/refil), FIO DENT (haste/flosser), ENXAG/ANTISSEPTICO BUCAL, DES/DESOD/DEO (aerosol, roll on, creme, pé, colônia), SAB/SABONETE (íntimo, esfoliante, facial, líquido/ML, barra), ABS (interno, seios, incontinência, diário, externo), PROT DIARIO, PROT/PROTETOR + SOLAR/FPS (labial, infantil, facial, kit, corporal), FRALD (geriátrica, pano/ecológica, pants, aberta), ESM (base/fortalecedor; não tinta/Acrilex/vitral), BASE + marca/termo de maquiagem → BASE FACIAL, BAT/BATOM (não batata), MAM, CHUP, PRESERV, DEMAQ, AGUA MICELAR, MAQ CORTAR, SECANTE de esmalte, LIXA (unha / pés), HENNA (sobrancelha/capilar), TINTURA/COLORACAO (kit), ALCOOL GEL, LENCO (umedecido: íntimo, facial/demaquilante, antisséptico, baby; seco/papel), COTONETE/HASTES FLEXIVEIS (não haste de ferramenta), ALGODAO, HID/HIDRATANTE/LOCAO/CREME P MAOS… (mãos, pés, labial, facial, banho, corporal), TALCO (pés), PERFUME/COLONIA/BODY SPLASH (feminino/masculino/unissex/corporal pelo texto), ESPUMA/CREME DE BARBEAR, POS BARBA, ACETONA/REMOVEDOR DE ESMALTE, AMOLECEDOR/CREME CUTICULA, ALICATE cutícula, CORTADOR DE UNHA, PINCA, CERA/FOLHA DEPILATÓRIA (facial/corporal), CREME DEPILATORIO, ESFOLIANTE (facial, mãos, pés, corporal), SERUM, TONICO, LAPIS (olho, boca, sobrancelha), RIMEL/MASCARA DE CILIOS, NECESSAIRE, OLEO + marca/termo capilar → OLEO CAPILAR, COPO de treinamento, CADEIRA de refeição, ANDADOR, ESCOVA de mamadeira, BICO de mamadeira, PRENDEDOR de chupeta.
- `infantilDe`: com marca/termo infantil (INFANTIL, KIDS, BABY, BEBE, JOHNSONS BABY, TURMA DA MONICA, PEPPA, FROZEN, TANDY, HIPOGLOS, BEPANTOL BABY…; não GIOVANNA BABY, BABYLISS) a categoria adulta vira a infantil (SHAMPOO → SHAMPOO INFANTIL, TALCO, SABONETE, HIDRATANTE, ÓLEO, COLÔNIA, PROTETOR SOLAR, CREME/ESCOVA DENTAL, LENÇO UMEDECIDO, KIT CAPILAR, ASSADURA, ESCOVA/PENTE, MAQUIAGEM, KIT, COPO).
- Farmácia intocada: a regra não troca item que o app pôs em categoria de FARMACIA, exceto DERMOCOSMETICO* com marca que não é de dermocosmético (NIVEA, SUNDOWN, NEUTROGENA voltam para PROTETOR SOLAR/HIDRATANTE; La Roche-Posay, Vichy, Avène, Eucerin, Bioderma, ISDIN, Cetaphil, CeraVe, Episol… ficam). Nenhum patch altera categoria de farmácia.
- Vocabulário (patch): puericultura leve/pesada, refeição infantil, kits (acessório infantil, banho, cuidados corporais, limpeza facial, dental, capilar, acessórios diversos), acessório de maquiagem/cosmética/unha, palito, cutelaria, designer de sobrancelha, sombra (paleta), rosto outros (pó solto, paleta), pós-depilação, secante de esmalte, escova/esponja de banho, assadura adulto x infantil, cuidados corporais (firmador, celulite), desodorante para os pés (Tenys Pé), óleo corporal, creme facial/olhos/gel/óleo facial, pincel de coloração, tesoura de cabelo, alisante, matizador, tratamento capilar, acessório de higiene dental, touca de banho. ROUPA INFANTIL, TALHER, PRATO, TESOURA, PINCEL, MOCHILA, AMENDOA, BUCHA E PARAFUSO, GELATINA, SECANTE PARA LOUCA, UTENSILIOS etc. excluem os termos de perfumaria que roubavam.
- Novas categorias na biblioteca: BALM PROTETOR SOLAR LABIAL, TRATAMENTO FACIAL, MAQUIAGEM OLHOS OUTROS.


## Catálogo Scanntech (Apti) e biscoito maisena (2026-10-22)
- `misturaCat` (pós-votação, depois de limpeza): produto seco para preparar pelo tipo no começo.
  - REFRESCO em G → SUCO EM PO; BEBIDA EM PO / MILK SHAKE (pó) → MODIFICADOR OUTROS.
  - PUDIM/FLAN/MOUSSE/MANJAR/MARIA MOLE/SORVETE em pó → MISTURA PO SOBREMESA (PO/SACHE escrito, ou marca registrada na DIMA em MISTURA EM PO/SOBREMESA PARA PREPARAR com até 60G ou 500G+; laticínio não conta).
  - BOLO + PO/MISTURA ou marca de mistura → MISTURA PO BOLO (INTEGRAL/ZERO/SEM GLUTEN → SAUDAVEL); PAO DE QUEIJO/BOLINHO DE CHUVA/PANQUECA → MISTURA PO OUTROS (marca de congelado não).
  - Granulado de chocolate, CONFEITO MICANGA/ESTRELINHA, açúcar colorido → CONFEITO GRANULADO; cereal cobertura/pastilhas de chocolate, açúcar de baunilha → CONFEITARIA OUTROS; SALAMONIACO → BICARBONATO.
  - AMACIANTE DE CARNE → TEMPERO INDUSTRIALIZADO (em ML: TEMPERO LIQUIDO); limpezaCat não pega mais amaciante com CARNE/AVES/TEMPERO.
  - TEMPERO… no começo → TEMPERO INDUSTRIALIZADO (POTE/MOLHOS não mandam).
  - Especiarias/ervas secas (curry, endro, anis, cravo, noz moscada, pimenta em grão, alho frito, cebola crispy…) → TEMPERO NATURAL/ESPECIARIA; alho/cebola/erva fresca só com seco escrito (SACHE, TUBO, GRANULADO, FRITO…) e nunca CONG/ROXO/IN NATURA.
  - FAROFA no começo que caiu em FARINHA → FAROFA.
  - BISC/BISCOITO/BOLACHA + MAIZENA/MAISENA/MAIZ (ou MAIS logo depois) → BISCOITO MAISENA (não recheado/wafer/cookie/amanteigado). Amido MAIZENA continua AMIDO DE MILHO.
- Caixa de caixas no DUN-14 (`caixaNiveis`): "8 X 15 X 20G" → 120X20G; "24 X 10 X 5 PACK" → 1200UN. "5 PACK" / "10 X 5 PACK" = unidades.
- consts: `marcasNovas` (marcas que a DIMA não tem: APTEA, APTIPOWER, CHOCOTEEN, CHOCOTRIX, SLESH, APTIVA, YEBA, TEMPERAPTI, APTI extra), `marcaNaoFrase` (CRAVO DA INDIA, MARIA MOLE, FAMILIA antes do peso, TEMPER depois de FAROFA… não são marca), `inicioFrases` (MARIA MOLE, PAO DE QUEIJO, BOLINHO DE CHUVA, MILK SHAKE… como início do descritivo), PHRASE NOZ MOSCADA / PIMENTA MISTA.
- libPatch `scanntech-2026-10` (agora aceita `inicio`): COCO RALADO começava com "FAROFA" → "COCO RALADO"; vocabulário de especiarias, bicarbonato, suco em pó, massa instantânea, biscoito maisena.
- Testado e descartado: aceitar marca pelo fabricante (APTIVA via APTI ALIM.) trazia RED, LIMP, VARAL… como marca.

## Tipo do biscoito com abreviação (2026-10-23)
- Causa: com "BISC" abreviado no começo nenhuma categoria de biscoito votava (o tipo RECHEADO, AMANTEIGADO… não era reconhecido) e a tabela de tipos mandava para BISCOITO OUTROS.
- `biscoitoCat` (dentro de `misturaCat`): BISC/BISCOITO(S)/BOLACHA nas 3 primeiras palavras (BOL só como 1ª) + tipo, na ordem WAFER/WAF, RECHEADO/RECH, COOKIE, TORTINHA, COBERTO/COB, AMANTEIGADO/AMANTEIG/AMANT/MANTEIGA/BUTTER, ROSCA/ROSQUINHA/ROSQ, SEQUILHO/SEQ, CHAMPANHE/CHAMP, AGUA E SAL/CRACKER, MAISENA/MAIZENA/MARIA, POLVILHO/POLV, PALITO, BIJU, LEITE (não LEITE COND), SALGADO/SALG, INTEGRAL/ZERO/FIT… (SAUDAVEL), CASEIRO. Biscoito para cachorro/pet não entra. ROSCA sem BISC (pão doce) fica como estava.
- PHRASE: BISC CHAMP → BISCOITO CHAMPANHE (antes virava CHAMPIGNON no descritivo), BISC AMANT/ROSQ/SEQ/POLV/WAF/RECH por extenso.
- BISCOITO ROSCA (e BOLACHA ROSCA, BISCOITOS ROSCAS, ROSCA BISCOITO) → BISCOITO ROSQUINHA. Descritivo das categorias de biscoito sem repetir o tipo nem BOLACHA/BISC (REMOVER_PATCH: ROSCA/ROSQ em ROSQUINHA, AMANT/AMANTEIG em AMANTEIGADO, RECH, WAF, SEQ, POLV, CHAMP, SALG, COOKIES): "BISCOITO ROSQUINHA MABEL LEITE 400G".
- Arquivo com BISCOITO OUTROS (ou categoria fora dos biscoitos) e descrição com o tipo: o tipo vence (flag BISCOITO_TIPO, tratada como regra forte em `categoriaArquivo`; categoria de biscoito específica do arquivo continua valendo). ROSCA vem antes de AMANTEIGADA e POLVILHO ("ROSCA AMANTEIGADA", "ROSCA DE POLVILHO" → ROSQUINHA). POL = polvilho; XISC (erro de digitação de BISC) conta como biscoito.
- BOL sozinho não conta como biscoito (era "BOL RECH BOLIM DE MINAS TILAPIA", bolinho). Item sem descrição não quebra a regra (travava a classificação de 30 mil itens no modo só descritivo).

## Massa instantânea (2026-10-23)
- `massaInstCat`: palavra de massa (MASSA, MAC, MACARRAO, LAMEN, RAMEN, RAMYUN, NOODLE(S), MIOJO, UDON, YAKISSOBA, BULDAK) + INST/INSTANTANEO ou LAMEN/RAMEN/RAMYUN/NOODLE/MIOJO → MASSA INSTANTANEA TRADICIONAL (COPO/CUP/XICARA → MASSA INSTANTANEA COPO; BOWL fica TRADICIONAL). Não vale começando com SOPA, CREME, CALDO, COLA, CAFE, FERMENTO… nem tigela/bowl de cozinha. Flag MASSA_INST vence a categoria do arquivo que não é massa instantânea (MASSA TRADICIONAL, PRODUTOS ORIENTAIS, RECIPIENTE).
- marcaAlias SHIN RAMYUN / NONG SHIM → NONGSHIM. Descritivo sem MASSA TRADICIONAL MAC INST depois do início (REMOVER_PATCH).

## Descritivo de AZEITONA (2026-10-23)
- Só na categoria AZEITONA: AZEITONA + informações complementares + MARCA + quantidade (a marca vai depois das informações).
- Abreviações (`azeitonaComp`): INTEIRA=INT, RECHEADA=RECH, FATIADA=FAT, SEM CAROCO=S/C, COM CAROCO=C/C, VIDRO=VD, SACHE=SCH. VIDRO/SACHE (que o app trata como embalagem) voltam como VD/SCH logo depois das abreviações. VD com outra cor na descrição (PRETA FATIADA VD) é vidro; sozinho (AZ VD) continua VERDE.
- Ex.: "AZEITONA VERDE SEM CAROCO VIDRO LA PASTINA 200G" → "AZEITONA VERDE S/C VD LA PASTINA 200G".

## Mel e própolis (2026-10-23)
- Causa: as categorias de mel só reconheciam a frase inteira (MEL POLIFLORAL, MEL SILVESTRE…); "MEL" sozinho e os nomes de florada não votavam, e outras palavras ganhavam (MEL BISNAGA → PAO BISNAGA, MEL ASSA PEIXE → PEIXE, MEL FLOR DE LARANJEIRA → PLANTA E FLOR, COMPOSTO… GUACO → ERVA CHA).
- `melCat` (flag MEL_TIPO, vence categoria do arquivo que não é de mel; farmácia intocada): o mel é o produto (MEL no começo, FAVO DE MEL, COMPOSTO… MEL, EXTRATO/EXT/PROPOLIS no começo), nunca sabor (sorvete, iogurte, biscoito, pão de mel, shampoo, mostarda, bala, granola, cereal, melado, Karo…). Ordem: COMPOSTO DE MEL (composto ou mel com própolis/guaco/agrião/gengibre/limão/romã…) > MEL COM FAVO > EXTRATO DE PROPOLIS > MEL ORGANICO > MEL MONOFLORAL (monofloral ou florada: eucalipto, laranjeira, assa-peixe, angico, aroeira, cipó-uva, acácia, manuka, jataí…) > MEL POLIFLORAL (silvestre, multifloral, puro, mel comum).
- Marca: produto não é marca (marcaNaoFrase: EXTRATO DE PROPOLIS, PROPOLIS VERDE, PROPOLIS, FAVO DE MEL no começo/depois de MEL, ROMA depois de COM/E, AROEIRA depois de MEL); BAIANINHO cadastrada em MEL (marcasNovas).
- Ajuste depois das regressões: MEL só é o produto como 1ª palavra, depois de BISNAGA/POTE/SACHE (DE) MEL ou depois de marca registrada em MEL na DIMA (BAIANINHO MEL PURO). MEL como cor/nome no meio (AZALEIA MEL sandália, TRAVESSA MEL, COLHER MEL, QJO MEL PRATO, PAOZINHO MEL, RAPADURA C MEL) não. Massa: LAMEN/NOODLES sem INST acima de 300G (macarrão para lamen 500G/1KG) não é instantâneo.

## Garrafa térmica (2026-10-26)
- `garrafaTermicaCat` (flag GARRAFA_TERMICA, vence GARRAFA OUTROS/TERMICO OUTROS do arquivo): GARRAFA/GF/BULE/TERMO/TERMOS/AMPOLA/REFIL GARRAFA/TERMICA no começo + TERMICA/TERM/ISOTERMICA/INOX/PAREDE DUPLA/VACUO/PRESSAO/TERMOS ou marca térmica (STANLEY, TERMOLAR, INVICTA…); marca térmica antes do tipo (TERMOLAR GARRAFA); SQUEEZE térmico. Não vale para caneca, copo, caixa, bolsa, lancheira, cuia, bebida; AMPOLA/TERMO só com TERMICA/INOX (ampola de tratamento, termo de garantia, termômetro ficam fora).
- Marca: TERMICA/TERMICO/ISOTERMICA/MAGIC PUMP nunca são marca (marcaNaoFrase); TERMOLAR/INVICTA saíram do vocabulário da categoria (eram tipo, não marca); MOR vale como marca no bazar (é GENERIC = morango no resto).
- Conteúdo: GARRAFA TERMICA é sempre em UN (1UN; pack 12X1L → 12UN; KIT 2 / C/2 UNIDADES → 2UN). A litragem (1L, 500ML) vai para o complemento, antes do conteúdo: "GARRAFA TERMICA INVICTA PRETA 1L 1UN". REFIL fica no descritivo.

## Garrafas em geral: conteúdo em UN (GARRAFA OUTROS e SQUEEZE também)
- Pedido: a regra da garrafa térmica vale para todas as garrafas. Em GARRAFA TERMICA, GARRAFA OUTROS e SQUEEZE (`GARRAFA_UN` em src.html) o conteúdo é sempre a unidade: 1UN, kit/jogo (KIT 2 → 2UN) ou caixa de 14 dígitos (C/12 → 12UN). A litragem (500ML, 1L) vai só no complemento do descritivo.
- `KIT n` também vale quando a quantidade já saiu 1UN.
- GARRAFA OUTROS começando por GARRAFAO: início GARRAFAO (não repete "GARRAFA GARRAFAO").
- Exemplos: GARRAFA SQUEEZE ALUMINIO 750ML 1UN · GARRAFA ROLHA 1L 1UN · GARRAFAO AGUA 5L 1UN.

## Função "Padronizar descritivo + sugestões" (botão separado no passo 4)
- Pedido: uma função à parte que só padroniza o descritivo e traz colunas de sugestão, sem mexer em nenhuma coluna do arquivo.
- Saída (`buildSugWorkbook`): a planilha do arquivo exatamente como veio (todas as colunas e cabeçalhos, `it.row` / `data.hdr`) + DESCRITIVO PADRONIZADO, MARCA SUGERIDA, FABRICANTE SUGERIDO, QUANTIDADE SUGERIDA, CATEGORIA SUGERIDA + aba RESUMO. Arquivo: BACKLOG_DESCRITIVO_SUGESTOES.xlsx.
- `runSugestao`: passada 1 = app livre (sugestão de quantidade/categoria); passada 2 = `passe.fixo` (descritivo com a categoria do arquivo, nunca trocada; quantidade do arquivo, 1UN do arquivo não é trocado pela descrição; número sem medida diferente do peso da descrição = UN; mesmo total = pack da descrição; UNIDADES x CONTENIDO UNITARIO do arquivo vira o pack 12X395G).
- Marca no modo fixo: votação por descrição (`findBrand` em cada descrição + marca da DIMA escrita em 2+ descrições; marca cortada no fim conta: ALTO GI, RIO; marca contida em outra perde: MAKE x MAKE ONE). Vale a mais citada (2+ descrições, ou a 1ª descrição se a marca é do segmento). Marca do arquivo escrita na descrição: fica a do arquivo, sem sugestão.
- Sugestões só quando diferem do arquivo: fabricante igual com outra grafia (NESTLE x NESTLE CIA) não conta; quantidade só com 2+ descrições trazendo o mesmo número; categoria só se a do arquivo não bate com a descrição E (o nome inteiro da categoria do app está na descrição OU a descrição bate e a marca é da categoria na DIMA). Arquivo vazio: a sugestão preenche.
- Leitura do arquivo: coluna CONTENIDO (total) tem prioridade sobre CONTENIDO UNITARIO; UNIDADES e CONTENIDO UNITARIO são lidas (`arqUn`, `arqCu`).
- Cutelaria (vale também no Classificar normal): CUTELARIA OUTROS começa com o tipo + DE UNHA / DE CUTICULA (CORTADOR DE UNHA, TESOURA DE UNHA, RASPADOR DE UNHA, LIXA DE UNHA, PALITO DE UNHA, ESPATULA DE CUTICULA; LIXA de pé, tesoura de cabelo e cortador de calos ficam fora); UNHA/CUTICULA/P/PARA saem do complemento; abreviações por extenso (PEQ, GDE, INF, CAB, MET, IMPORT, EMBORR, ESP, LAM, DOBR); CM/MM sem número e REF saem.
- marcaNaoFrase: UNI / UNID depois de número ("COM 3 UNI") não é marca.
- Teste: `testes/testar_sugestao.js` com `testes/sugestao_exemplo.xlsx` (colunas do arquivo idênticas + 14 linhas esperadas): 31/31. testar_regras 821/821.
- Regra da marca no descritivo (pedido do usuário): o descritivo usa a marca, a quantidade e a categoria do arquivo; só quando o arquivo traz OUTRA MARCA o descritivo usa a MARCA SUGERIDA. No modo fixo isso vale também na farmácia e com marca de personagem (sem troca pela da descrição). Com marca no arquivo, a marca sugerida (outra) sai do complemento: CORTADOR DE UNHA BELLIZ GRANDE, não BELLIZ RICCA. Conferido no testar_sugestao.js (linha a linha).

## Descritivo sem palavras repetidas em outra forma (vale em todos os modos)
- Pedido: "GARRAFA TERMICA ALADDIN TERMICO AZEITONA 1L 6X1UN" trazia TERMICA e TERMICO; também ALADDIN e ALADIN no mesmo descritivo.
- `semVariantes` (antes de montar o descritivo): tira do complemento a palavra que repete o início ou outra palavra do complemento em outro gênero/plural (TERMICO x TERMICA, RECHEADA x RECHEADO, CREMOSO x CREMOSA) e a que é a marca com grafia parecida (letra dobrada ou 1 letra de diferença: ALADIN x ALADDIN, NESTLLE x NESTLE, BAIANA x BAHIANA).
- Não mexe em palavras com menos de 4 letras (DE, COM), números/medidas; gênero/plural não é comparado com a marca (FLORES fica com APIS FLORA).
- Impacto medido nos 821 exemplos ensinados: 5 descritivos mudaram, todos tirando repetição; CUTELARIA_2: nenhum. testar_sugestao 53/53 (com a garrafa ALADDIN e o biscoito NESTLLE).

## Descritivo + sugestões: UNIDADES SUGERIDA e CONTENIDO UNITARIO SUGERIDO
- Colunas novas logo depois de QUANTIDADE SUGERIDA (ordem: DESCRITIVO, MARCA, FABRICANTE, QUANTIDADE, UNIDADES, CONTENIDO UNITARIO, CATEGORIA) e contadas na aba RESUMO.
- Vêm da passada 1 (qn / quv do app) e só quando diferem do arquivo (UNIDADES / CONTENIDO UNITARIO lidos em `arqUn` / `arqCu`; coluna ausente = sugere).
- Saem junto com a QUANTIDADE SUGERIDA, ou, com o mesmo total, quando o pack (n unidades) está escrito em 2+ descrições (ou na única) ou o código tem 14 dígitos: arquivo 1 x 4740 com "12X395G" -> 12 e 395. Quantidade padrão (1UN sem informação) não gera sugestão.
- testar_sugestao 56/56 (lixa C/6 -> CU 6; arroz sem dados -> 1 e 5000; leite condensado 1x4740 -> 12 e 395).
