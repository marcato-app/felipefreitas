# Gera os JSON das regras e dicionários de Farmácia para usar no AppGen.
#   node farma_appgen/extrai_listas.js farma_appgen/_listas.json && python3 farma_appgen/gera_json.py && rm farma_appgen/_listas.json
# Saídas: farma_appgen/farma_regras.json (algoritmo + regras + listas + categorias)
#         farma_appgen/farma_dicionarios.json (fabricantes, siglas, marcas, princípios ativos, EST MER 7)
import json, os, datetime
D = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(D, '..', 'consts.json')))
L = json.load(open(os.path.join(D, '_listas.json')))

OF, OM, OC = 'OUTRO FABRICANTE', 'OUTRA MARCA', 'OUTRA CATEGORIA'

pipeline = [
    {'passo': 1, 'id': 'normalizar', 'nome': 'Normalizar descrições',
     'faz': 'Junta as descrições do código de barras (arquivo + lojas/PDV + CMED). MAIÚSCULAS, sem acento e pontuação. A coluna do código aceita barcode, código de barras, EAN ou SKU; a da descrição aceita descriptions ou descritivo.',
     'saida': 'textos normalizados (T)'},
    {'passo': 2, 'id': 'base_anvisa', 'nome': 'Base Anvisa (código de barras)',
     'faz': 'Procura o código em: lista PMC da CMED atual → edições anteriores (2021 em diante) → dados abertos de preços da Anvisa (TA_PRECOS_MEDICAMENTOS). Achou: produto, apresentação, laboratório e classe oficiais entram como descrição principal e BASE ANVISA = SIM (não precisa validar). Não achou: NÃO.',
     'saida': 'baseAnvisa, cmed'},
    {'passo': 3, 'id': 'categoria_arquivo', 'nome': 'Categoria informada',
     'faz': 'A categoria do arquivo vale. Só sai se a descrição apontar outra cesta e não tiver sinal de farmácia. Sinal fraco também segura em Farmácia (regex REGEX.RX_FARMA_ARQ: spray, pastilha, própolis, reidratante, agulha descartável, dentadura, bengala, SUPL ALIM...). Palavra de sabor (ABACAXI, LIMAO, BALA, TEMPERO) nunca tira item da Farmácia.',
     'usa': ['categorias', 'listas.REGEX.RX_FARMA_ARQ', 'listas.REGEX.RX_SINAL_FARMA'], 'saida': 'categoria'},
    {'passo': 4, 'id': 'regras_categoria', 'nome': 'Categoria pela descrição',
     'faz': 'Ordem: termo forte de balcão (listas.REGEX.OTC) → marca da base do cliente (marca em várias categorias = a de maior venda; antifúngico explícito ganha) → produto CMED mais específico → princípio ativo → DIMA.',
     'usa': ['listas.REGEX.OTC', 'dicionarios.marcasHoja', 'dicionarios.principiosAtivos', 'dicionarios.marcasDima'], 'saida': 'categoria'},
    {'passo': 5, 'id': 'cmed_classe', 'nome': 'Classe oficial da CMED',
     'faz': 'Código na Base Anvisa: a classe oficial (EphMRA) decide quando o app deu outro grupo ATC E também a subcategoria quando a classe traz o 5º dígito (A2B2 → A02B2, não A02B1). Código fora da base: procura a MESMA APRESENTAÇÃO na lista atual (2025+): mesmo produto, mesma dose e mesma forma (FORMAS_AP), de preferência do mesmo laboratório (prefixo de 7 dígitos do código). Classe única → vale para o item. Só corrige item que já é remédio (suplemento/correlato nunca vira remédio por aqui).',
     'usa': ['listas.REGEX.FORMAS_AP'], 'saida': 'categoria'},
    {'passo': 6, 'id': 'antifungico_pele', 'nome': 'Antifúngico de uso na pele',
     'faz': 'Categoria em ANTIF_OUTRA (G01B, J02A, A01B, D11A, D03A9) + forma de pele (RX_PELE) + nada de vaginal/oral/shampoo (RX_NAO_PELE) + princípio antifúngico (RX_ANTIF_PA, na descrição ou na substância CMED) ou marca com D01A1 na base (marcasAntifungicoPele) → D01A1. G01B exige DERMATOLOGICO ou forma não-creme (RX_PELE_FORTE); D11A/D03A9 exigem dose.',
     'usa': ['listas.REGEX.ANTIF_OUTRA', 'listas.REGEX.RX_PELE', 'listas.REGEX.RX_PELE_FORTE', 'listas.REGEX.RX_NAO_PELE', 'listas.REGEX.RX_ANTIF_PA', 'dicionarios.marcasAntifungicoPele'], 'saida': 'categoria'},
    {'passo': 7, 'id': 'correcoes_categoria', 'nome': 'Tabela de correções de categoria',
     'faz': 'Depois da CMED: cada linha de dicionarios.correcoesCategoria é [regex, código EphMRA, motivo]. A 1ª regex que bate na descrição troca a categoria (só em item que já é remédio). Ex.: OMEPRAZOL/PANTOPRAZOL → A02B2, NEOSALDINA/DORALGINA → A03D, MINOXIDIL solução → D11A, DIPROSPAN → H02A1, ENGOV AFTER → A07G.',
     'usa': ['dicionarios.correcoesCategoria'], 'saida': 'categoria'},
    {'passo': 8, 'id': 'vitamina', 'nome': 'Vitamina e mineral',
     'faz': 'Suplemento (SUPL, SUPLEMENTO, A-Z ou marca de vitamina) vai para VITAMINA OUTRO ou MULTIVITAMINICO (A-Z/polivitamínico ou 3+ nutrientes = MULTIVITAMINICO). Remédio registrado fica na categoria de remédio.',
     'usa': ['dicionarios.vitaminas', 'listas.VIT_NAO'], 'saida': 'categoria'},
    {'passo': 9, 'id': 'fabricante', 'nome': 'Fabricante',
     'faz': 'Laboratório da descrição (nome ou sigla "(XXX)" no fim) ou da CMED → DIMA → Hoja → vitaminas. O FABRICANTE DO ARQUIVO VENCE quando já existe na base (Hoja, DIMA, vitaminas, cadastrados) ou quando a sigla da descrição foi gerada dele (PROCTER "(PRO)"). Nome sempre canônico; nunca cria fabricante se já existe parecido.',
     'usa': ['dicionarios.fabricantes', 'dicionarios.siglas', 'dicionarios.codigosLab', 'listas.FAB_LIXO', 'listas.FAB_ALIAS'], 'saida': 'fabricante'},
    {'passo': 10, 'id': 'marca', 'nome': 'Marca',
     'faz': 'Marca do arquivo (se válida) → DIMA → Hoja → vitaminas → nome do produto na CMED → nome comercial escrito → princípio ativo (genérico). Nunca palavra de FARMA_NAO_MARCA (inclui TUTTI, FRUTTI, CLO, DICLOR, AMOX, UNIAO), forma (XAROPE, POMADA), laboratório ou número.',
     'usa': ['dicionarios.marcasDima', 'dicionarios.marcasHoja', 'listas.FARMA_NAO_MARCA', 'listas.PALAVRA_DESCRITIVA'], 'saida': 'marca'},
    {'passo': 11, 'id': 'sigla', 'nome': 'Sigla (obrigatória em Farmácia, menos dermocosmético)',
     'faz': '"(XXX)" escrito → código do laboratório → sigla da marca na Hoja → sigla do fabricante → gerada (3 letras). Sem fabricante → OTF. Siglas do mesmo grupo valem para o fabricante do grupo (GER/LEG/NVQ → EMS PHARMA; NEO → HYPERA PHARMA).',
     'usa': ['dicionarios.siglas'], 'saida': 'sigla'},
    {'passo': 12, 'id': 'conteudo', 'nome': 'Conteúdo',
     'faz': 'Antes de ler: tira preço (PMC 21.00), lote (L 70250, LOTE...), FCI, código com zero à esquerda (04502), faixa de peso do animal (10,1 A 20KG), "C30 L" (L de limão), "D3L90". Depois: número do arquivo achado como quantidade numa descrição vale (30 CPR, C/90, 200 DOSES), menos denominador da dose (375MG/5ML, 7MG X 1 ML); conteúdo do arquivo 5x maior que o que 2+ descrições concordam (1000 = dose) perde; caixa fechada em Farmácia (N≥6, unidade ≥30 ML/G: 24X120ML) = a unidade, sachê 16X5G fica; bombinha/spray (120X17.5ML) = doses; remédio em MG com KG na descrição = contagem; mesmo número em G e em comprimidos = contagem. Sempre com unidade; sem nada: 1UN.',
     'usa': ['listas.UN_CONTA'], 'saida': 'conteudo'},
    {'passo': 13, 'id': 'descritivo', 'nome': 'Descritivo padronizado',
     'faz': 'Início da categoria (SUPL ALIM [MULT]) ou marca + complemento + dose + quantidade na forma (10CPRS, 28CPS, 30ML, 200DOSES) + "(SIGLA)". Máx. 60 caracteres (corta complemento, nunca marca/dose/quantidade/sigla).',
     'usa': ['categorias[].inicio', 'categorias[].remover'], 'saida': 'descritivo'},
    {'passo': 14, 'id': 'genericos', 'nome': 'Sigla do genérico = sigla do fabricante',
     'faz': 'Marca genérica (princípio ativo + sigla): se a sigla não é do fabricante da linha (nem do grupo), troca pela dele, no descritivo também (AMBROXOL MED com TEUTO → AMBROXOL TEU).',
     'saida': 'marca, descritivo'},
    {'passo': 15, 'id': 'outra_marca', 'nome': 'Fabricante conhecido nunca fica com OUTRA MARCA',
     'faz': 'Em todas as cestas: marca OUTRA MARCA com fabricante conhecido (fora CODIGO INTERNO) → marca = nome curto do fabricante (+ sigla em Farmácia). OUTRA MARCA só existe com OUTRO FABRICANTE.',
     'saida': 'marca'},
    {'passo': 16, 'id': 'unificar', 'nome': 'Uma marca = um fabricante',
     'faz': 'Passada no arquivo inteiro. Dono da marca, nesta ordem: fabricante dono da sigla da marca (aceita sigla do grupo) → fabricante da marca na base do cliente → fabricante com o nome da marca que existe na base (MERCUR → MERCUR SA) → fabricante do arquivo que existe na base → DIMA → mais comum. Linhas de outro fabricante: genérico ganha a sigla do próprio laboratório; produto CMED com outro nome ganha a marca da CMED; fabricante do arquivo existente com marca achada por palavra solta volta à marca do arquivo (+ sigla); senão o fabricante vira o dono.',
     'saida': 'marca, fabricante'},
    {'passo': 17, 'id': 'codigo_interno', 'nome': 'Produtos distintos no código',
     'faz': 'Descrições do mesmo código de produtos de OUTRA CESTA (sem nome em comum) → CODIGO INTERNO, OUTRA MARCA, OUTRO FABRICANTE + coluna PRODUTOS DISTINTOS NO CODIGO ("SIM: ..." ou "VERIFICAR: ...").',
     'usa': ['constantes.CODIGO_INTERNO'], 'saida': 'categoria, marca, fabricante, produtosDistintos'},
    {'passo': 18, 'id': 'status', 'nome': 'STATUS de cadastro',
     'faz': 'CRIAR MARCA / CRIAR FABRICANTE / CRIAR MARCA E FABRICANTE / SEM FABRICANTE / CRIAR MARCA; SEM FABRICANTE. Fabricante novo vai para a aba FABRICANTES NOVOS com os nomes parecidos que já existem.',
     'saida': 'status'},
    {'passo': 19, 'id': 'est_mer', 'nome': 'Código EST MER 7', 'faz': 'Código da categoria pela tabela estMer7.', 'usa': ['dicionarios.estMer7'], 'saida': 'estMer7Codigo'},
]

regras = [
    {'id': 'FAB-01', 'tema': 'fabricante', 'regra': 'Um nome só por fabricante; usar sempre o nome canônico.'},
    {'id': 'FAB-02', 'tema': 'fabricante', 'regra': 'Nome que já existe na base sempre ganha de nome novo. Prioridade da escrita: DIMA → Hoja → vitaminas. Fabricante novo tem no máximo 2-3 palavras.'},
    {'id': 'FAB-03', 'tema': 'fabricante', 'regra': 'Fabricante do arquivo que já existe na base vence o laboratório da descrição/CMED e a unificação (MERCUR não vira MERCK; BAND-AID não vira OPHTHALMOS).'},
    {'id': 'FAB-04', 'tema': 'fabricante', 'regra': 'Palavra descritiva/genérica nunca é fabricante (ANTIBIOTICOS, VITAMINA, FARMA). SIN PROVEEDOR ASOCIADO nunca é fabricante.'},
    {'id': 'MAR-01', 'tema': 'marca', 'regra': 'Uma marca = um fabricante no arquivo inteiro (passo 16). Genérico se separa pela sigla.'},
    {'id': 'MAR-02', 'tema': 'marca', 'regra': 'Sigla OBRIGATÓRIA no fim da marca de Farmácia (menos dermocosmético). Sigla do genérico = sigla do fabricante da linha ou do seu grupo.'},
    {'id': 'MAR-03', 'tema': 'marca', 'regra': 'Fabricante conhecido nunca fica com OUTRA MARCA. OUTRA MARCA só com OUTRO FABRICANTE.'},
    {'id': 'MAR-04', 'tema': 'marca', 'regra': 'Forma (XAROPE, POMADA, CREME...) não entra na marca. Genérico sem fabricante → "<PRODUTO> OTF".'},
    {'id': 'MAR-05', 'tema': 'marca', 'regra': 'Suplemento com nome de remédio (ex.: "MOUNJARO" natural em cápsula) não é a marca do remédio nem o fabricante dele.'},
    {'id': 'CAT-01', 'tema': 'categoria', 'regra': 'A classe oficial da CMED decide o grupo e a subcategoria (5º dígito) do remédio; sem o código na CMED, vale a mesma apresentação (produto + dose + forma).'},
    {'id': 'CAT-02', 'tema': 'categoria', 'regra': 'Correções manuais em dicionarios.correcoesCategoria valem depois da CMED (só para item de remédio).'},
    {'id': 'CAT-03', 'tema': 'categoria', 'regra': 'Antifúngico em forma de pele → D01A1 (passo 6). Soro fisiológico nasal → R01A9; nafazolina → R01A7.'},
    {'id': 'CAT-04', 'tema': 'categoria', 'regra': 'Item que o arquivo diz Farmácia não sai para outra cesta por palavra de sabor ou de uso comum quando tem sinal de farmácia (RX_FARMA_ARQ).'},
    {'id': 'CON-01', 'tema': 'conteudo', 'regra': 'Preço, lote, FCI, código e peso do animal não são conteúdo. Caixa fechada = unidade; bombinha = doses; conteúdo inflado do arquivo perde para as descrições.'},
    {'id': 'ANV-01', 'tema': 'base_anvisa', 'regra': 'BASE ANVISA = SIM quando o código está na CMED (qualquer edição) ou nos dados abertos de preços: produto, apresentação e laboratório oficiais, não precisa validar. NÃO = validar. Anvisa não publica código de barras de cosmético, alimento, suplemento ou correlato.'},
    {'id': 'COD-01', 'tema': 'codigo_interno', 'regra': 'Produtos distintos no mesmo código → CODIGO INTERNO, OUTRA MARCA, OUTRO FABRICANTE + PRODUTOS DISTINTOS NO CODIGO.'},
    {'id': 'DES-01', 'tema': 'descritivo', 'regra': 'Marca + complemento + dose + quantidade/forma + "(SIGLA)". Máx. 60 caracteres. CPRS = comprimido/drágea, CPS = cápsula.'},
    {'id': 'STA-01', 'tema': 'status', 'regra': 'STATUS: CRIAR MARCA / CRIAR FABRICANTE / CRIAR MARCA E FABRICANTE / SEM FABRICANTE / CRIAR MARCA; SEM FABRICANTE.'},
    {'id': 'COR-01', 'tema': 'correcao', 'regra': 'Ao corrigir arquivo já classificado: mexer só nas linhas com problema e mostrar o antes → depois (coluna O QUE MUDOU).'},
]

cats = [{k: e.get(k) for k in ('nome', 'inicio', 'incluir', 'tambem', 'excluir', 'forte', 'remover', 'regra', 'unidadeSugerida')}
        for e in C['libSeed']['categorias'] if e.get('cesta') == 'FARMACIA']
of = C.get('nomesOficiais', {})
for e in cats:
    e['nomeOficial'] = of.get(e['nome'], e['nome'])
    e['estMer7'] = C['estMer7'].get(e['nomeOficial']) or C['estMer7'].get(e['nome'])

regras_json = {
    'versao': datetime.date.today().isoformat(),
    'descricao': 'Agente de Farmácia do Classificador de Backlog: algoritmo, regras e listas. Os dicionários estão em farma_dicionarios.json.',
    'entrada': {'codigoBarras': 'string', 'descricoes': 'lista de descrições do PDV/lojas', 'categoriaInformada': 'opcional', 'marcaInformada': 'opcional', 'fabricanteInformado': 'opcional'},
    'saida': {'colunas': ['CODIGO BARRAS', 'DESCRITIVO PADRONIZADO', 'FABRICANTE', 'MARCA', 'CONTENIDO', 'CATEGORIA', 'EST MER 7 CODIGO',
                          'CODIGO INTERNO', 'STATUS', 'PRODUTOS DISTINTOS NO CODIGO', 'BASE ANVISA', 'ORIGEM ANVISA']},
    'consultaRapida': {'entrada': 'linhas coladas do Excel: código (barcode/código de barras/EAN/SKU) e descrição (descriptions/descritivo), com ou sem cabeçalho; opcionais MARCA, FABRICANTE, CATEGORIA, CONTENIDO',
                       'saida': 'as colunas de saída + ANTES (o que veio colado) e O QUE MUDOU'},
    'constantes': {'OUTRO_FABRICANTE': OF, 'OUTRA_MARCA': OM, 'OUTRA_CATEGORIA': OC, 'SIGLA_SEM_FAB': L['SIGLA_SEM_FAB'],
                   'CODIGO_INTERNO': L['CODIGO_INTERNO'], 'CODIGO_INTERNO_EST_MER': '.3.10.1.1.3', 'DESCRITIVO_MAX': 60,
                   'NUNCA_MARCA': ['POR DEFECTO'], 'NUNCA_FABRICANTE': ['SIN PROVEEDOR ASOCIADO'],
                   'STATUS': ['CRIAR MARCA', 'CRIAR FABRICANTE', 'CRIAR MARCA E FABRICANTE', 'SEM FABRICANTE', 'CRIAR MARCA; SEM FABRICANTE']},
    'pipeline': pipeline,
    'regras': regras,
    'listas': {k: v for k, v in L.items() if k not in ('SIGLA_SEM_FAB', 'CODIGO_INTERNO')},
    'listasDescricao': {
        'FARMA_NAO_MARCA': 'nunca é marca em Farmácia',
        'PALAVRA_DESCRITIVA': 'descreve o produto; nunca é marca nem fabricante',
        'PN_FORA': 'palavras ignoradas ao montar o nome do produto',
        'LAB_LIXO': 'palavras retiradas do nome do laboratório antes de comparar (LTDA, LAB, FARMA...)',
        'FAB_LIXO': 'idem, para unificar nomes de fabricante',
        'FAB_ALIAS': 'apelido → nome canônico do fabricante',
        'LAB_NOME_NAO': 'palavras que sozinhas não identificam laboratório',
        'LAB_COD_NAO': 'códigos de 3 letras que não são sigla de laboratório',
        'VIT_NAO': 'palavras que não contam como nome de vitamina',
        'SAIS_DCB': 'sais do princípio ativo (não são marca)',
        'TIPO_SAUDE': 'correlatos de saúde',
        'CONNECT': 'conectivos',
        'UN_CONTA': 'regex das formas que contam como UN',
        'REGEX': 'regras em regex (texto da expressão, sintaxe JavaScript, aplicar na descrição normalizada): OTC = [regex, categoria]; FORMAS_AP = forma → regex',
    },
    'categorias': cats,
}

dic = {
    'versao': regras_json['versao'],
    'formatos': {
        'fabricantes': 'objeto: chave/variação do nome → nome canônico do fabricante',
        'siglas.fab': 'fabricante → sigla de 3 caracteres',
        'siglas.marcas': 'marca (sem sigla) → sigla usada na Hoja',
        'siglas.codigos': 'sigla/código → fabricante',
        'codigosLab': 'código de 3 letras → laboratório',
        'marcasHoja': 'lista [marca, categoria, fabricante, peso]',
        'marcasDima': 'lista [marca, categoria, cesta, peso]',
        'principiosAtivos': 'lista {pa, partes[], cat, validar, outras[]}: todas as partes precisam aparecer',
        'vitaminas': 'marcas de vitamina (fabricante, % multi), pesos de palavras MULTI x OUTRO, prior, fora (remédios), pref, fabVit',
        'estMer7': 'nome da categoria → código EST MER 7',
        'correcoesCategoria': 'lista [regex na descrição normalizada, código EphMRA da categoria certa, motivo] (passo 7)',
        'marcasAntifungicoPele': 'marcas que têm D01A1 na base do cliente (passo 6)',
    },
    'fabricantes': C['farmaFabs'],
    'siglas': C['farmaSiglas'],
    'codigosLab': C['farmaCodLab'],
    'marcasHoja': C['farmaMarcas'],
    'marcasDima': C['farmaDima'],
    'principiosAtivos': C['farmaPA'],
    'vitaminas': C['farmaVit'],
    'estMer7': C['estMer7'],
    'correcoesCategoria': [l.rstrip('\n').split('\t')[:3] for l in open(os.path.join(D, '..', 'dados', 'farma_correcoes_categoria.tsv'), encoding='utf-8') if l.strip() and not l.startswith('#')],
    'marcasAntifungicoPele': C.get('farmaMarcasD01', []),
}

for nome, obj in (('farma_regras.json', regras_json), ('farma_dicionarios.json', dic)):
    p = os.path.join(D, nome)
    json.dump(obj, open(p, 'w'), ensure_ascii=False, indent=1)
    print(nome, os.path.getsize(p) // 1024, 'KB')
print('categorias de Farmácia:', len(cats), '| sem código EST MER 7:', sum(1 for e in cats if not e['estMer7']))
