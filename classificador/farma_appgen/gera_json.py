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
     'faz': 'Junta todas as descrições do código de barras (PDV/lojas + arquivo), passa para MAIÚSCULAS, tira acento e pontuação.',
     'saida': 'textos normalizados (T)'},
    {'passo': 2, 'id': 'categoria_arquivo', 'nome': 'Categoria informada',
     'faz': 'Se o arquivo ou a IA trouxe categoria válida (CATEGORIA / Est Mer 7 Descripcion / sugestão), ela vale. Nunca OUTRA CATEGORIA quando há sugestão.',
     'usa': ['categorias'], 'saida': 'categoria'},
    {'passo': 3, 'id': 'cmed', 'nome': 'Remédio registrado (CMED)',
     'faz': 'Código de barras na lista CMED, ou marca CMED sem sinal de suplemento (SUPL, A-Z) → categoria do remédio (A11/A12/A13...).',
     'saida': 'categoria'},
    {'passo': 4, 'id': 'principio_ativo', 'nome': 'Categoria pelo princípio ativo',
     'faz': 'Procura os princípios ativos (todas as "partes" precisam aparecer). A regra mais específica ganha; empate = o que aparece primeiro. Produto veterinário (CAO, GATO, PET, VET) não vai para Farmácia humana.',
     'usa': ['dicionarios.principiosAtivos'], 'saida': 'categoria, principioAtivo'},
    {'passo': 5, 'id': 'vitamina', 'nome': 'Vitamina e mineral',
     'faz': 'Suplemento (SUPL, SUPLEMENTO, A-Z ou marca de vitamina) vai para VITAMINA OUTRO ou MULTIVITAMINICO. A-Z/polivitamínico ou 3+ nutrientes diferentes = MULTIVITAMINICO; 1 ou 2 = VITAMINA OUTRO. Pulado quando a categoria veio informada (passo 2).',
     'usa': ['dicionarios.vitaminas', 'listas.VIT_NAO'], 'saida': 'categoria'},
    {'passo': 6, 'id': 'balcao', 'nome': 'Balcão / fitoterápico / correlato',
     'faz': 'Termo forte → categoria (simeticona → A02A2, valeriana → N05B2, protetor solar → DERMOCOSMETICO SOLAR...). Ganha de palavra de sabor ou de outra cesta.',
     'usa': ['categorias'], 'saida': 'categoria'},
    {'passo': 7, 'id': 'nao_farma', 'nome': 'Não é Farmácia',
     'faz': 'Item que não é farma (escova de cabelo, café, bicicleta, luva...) sai para a categoria certa da outra cesta, com alerta.',
     'saida': 'categoria'},
    {'passo': 8, 'id': 'fabricante', 'nome': 'Fabricante',
     'faz': 'Ordem: laboratório escrito na descrição (nome ou sigla de 3 letras no fim) → fabricante da marca na DIMA → base Hoja → base de vitaminas → fabricante do arquivo. Nome sempre canônico (fabricantes: chave → nome único). Grupo: GERMED/LEGRAND → EMS PHARMA, NEO QUIMICA → HYPERA PHARMA.',
     'usa': ['dicionarios.fabricantes', 'dicionarios.siglas.codigos', 'dicionarios.codigosLab', 'listas.LAB_LIXO', 'listas.LAB_NOME_NAO', 'listas.LAB_COD_NAO', 'listas.FAB_LIXO', 'listas.FAB_ALIAS'],
     'saida': 'fabricante'},
    {'passo': 9, 'id': 'marca', 'nome': 'Marca',
     'faz': 'Cadeia: marca DIMA → marca Hoja (nome mais completo) → marca da base de vitaminas → nome comercial escrito na descrição → nome do produto (ex.: CHA VERDE, OLEO DE CARTAMO) → princípio ativo (genérico). Nunca palavra de listas.FARMA_NAO_MARCA, laboratório, sal, forma ou número; sem quantidade (54G sai).',
     'usa': ['dicionarios.marcasDima', 'dicionarios.marcasHoja', 'dicionarios.vitaminas.marcas', 'listas.FARMA_NAO_MARCA', 'listas.PALAVRA_DESCRITIVA', 'listas.PN_FORA', 'listas.SAIS_DCB', 'listas.CONNECT'],
     'saida': 'marca (sem sigla)'},
    {'passo': 10, 'id': 'sem_fabricante', 'nome': 'Item sem fabricante',
     'faz': 'Sem fabricante: tenta DIMA → base de vitaminas → Hoja pela marca. Genérico/nome de produto → fabricante OUTRO FABRICANTE e sigla OTF. Nome comercial sem fabricante em nenhuma base → a marca vira o próprio fabricante (STATUS CRIAR FABRICANTE).',
     'saida': 'fabricante'},
    {'passo': 11, 'id': 'sigla', 'nome': 'Sigla (obrigatória)',
     'faz': 'Ordem: "(XXX)" escrito no fim da descrição → código/nome do laboratório escrito → sigla da marca na Hoja (siglas.marcas) → código da marca na DIMA → sigla padrão do fabricante (siglas.fab) → gerada do nome (sempre 3 caracteres). Sem fabricante → OTF.',
     'usa': ['dicionarios.siglas', 'constantes.SIGLA_SEM_FAB'], 'saida': 'sigla'},
    {'passo': 12, 'id': 'marca_final', 'nome': 'Marca final',
     'faz': 'marca = <marca> + " " + <sigla> (ex.: NIMESULIDA GER, VITAMINA D3 BIO, VITAMINA C OTF). Dermocosmético: marca sem sigla. Item de Farmácia com fabricante conhecido nunca fica OUTRA MARCA.',
     'saida': 'marca'},
    {'passo': 13, 'id': 'conteudo', 'nome': 'Conteúdo',
     'faz': 'Sempre com unidade. Formas (COMP, CPR, CAPS, DRG...) contam como UN; líquidos/cremes em ML/G. Padrão Anvisa "X 30" no fim ganha de número colado. Sem nada: 1UN.',
     'usa': ['listas.UN_CONTA'], 'saida': 'conteudo'},
    {'passo': 14, 'id': 'descritivo', 'nome': 'Descritivo padronizado',
     'faz': 'Início fixo da categoria (SUPL ALIM, SUPL ALIM MULT...) ou marca/princípio ativo + complemento + dosagem + quantidade na forma (10CPRS, 28CPS, 30ML) + "(SIGLA)" no fim. Máx. 60 caracteres (corta complemento, nunca marca/dose/quantidade/sigla). Laboratório não entra. VITAMINA D3, B12, OMEGA 3, K2, Q10, A Z preservados.',
     'usa': ['categorias[].inicio', 'categorias[].remover'], 'saida': 'descritivo'},
    {'passo': 15, 'id': 'unificar', 'nome': 'Unificar marca × fabricante',
     'faz': 'Passada final em todos os itens: uma marca tem um fabricante só (o majoritário); genéricos ficam separados pela sigla.',
     'saida': 'marca, fabricante'},
    {'passo': 16, 'id': 'codigo_interno', 'nome': 'Produtos distintos no código',
     'faz': 'Se as descrições do mesmo código são de produtos diferentes (de outra cesta, sem semelhança de nome: menos de 2 palavras em comum e 1ª palavra diferente) → CATEGORIA CODIGO INTERNO, OUTRA MARCA, OUTRO FABRICANTE e coluna PRODUTOS DISTINTOS NO CODIGO = "SIM: ..." (ou "VERIFICAR: ...").',
     'usa': ['constantes.CODIGO_INTERNO'], 'saida': 'categoria, marca, fabricante, produtosDistintos'},
    {'passo': 17, 'id': 'status', 'nome': 'STATUS de cadastro',
     'faz': 'CRIAR MARCA se a marca não existe nas bases; CRIAR FABRICANTE se o fabricante não existe; CRIAR MARCA E FABRICANTE; SEM FABRICANTE quando ficou OUTRO FABRICANTE (CRIAR MARCA; SEM FABRICANTE se a marca OTF é nova).',
     'saida': 'status'},
    {'passo': 18, 'id': 'est_mer', 'nome': 'Código EST MER 7',
     'faz': 'Código da categoria pela tabela estMer7 (por nome oficial, nome do app ou código ATC).',
     'usa': ['dicionarios.estMer7'], 'saida': 'estMer7Codigo'},
]

regras = [
    {'id': 'FAB-01', 'tema': 'fabricante', 'regra': 'Um nome só por fabricante (nada de CIMED A / CIMED B). Usar sempre o nome canônico do dicionário.'},
    {'id': 'FAB-02', 'tema': 'fabricante', 'regra': 'Prioridade do nome: DIMA → Hoja (tem erros; buscar o parecido, ex. ACHE LABORATORIOS → ACHE) → base de vitaminas.'},
    {'id': 'FAB-03', 'tema': 'fabricante', 'regra': 'Antes de criar fabricante, conferir no Hoja se já existe com outra escrita (HIDRA LISE = HIDRALISE) ou se o nome é marca de outro fabricante (GOOD VIT → GOMES SUPLEMENTOS).'},
    {'id': 'FAB-04', 'tema': 'fabricante', 'regra': 'Palavra descritiva (listas.PALAVRA_DESCRITIVA), ingrediente ou nome de produto nunca é fabricante.', 'exemplos': ['HOMEM', 'VEGANO', 'COMPLEXO', 'TRIBULUS', 'LEVEDO DE CERVEJA']},
    {'id': 'FAB-05', 'tema': 'fabricante', 'regra': 'Sem fabricante identificado → OUTRO FABRICANTE. SIN PROVEEDOR ASOCIADO nunca é fabricante.'},
    {'id': 'FAB-06', 'tema': 'fabricante', 'regra': 'Laboratório do grupo sai pelo grupo: GERMED/LEGRAND → EMS PHARMA; NEO QUIMICA → HYPERA PHARMA.'},
    {'id': 'MAR-01', 'tema': 'marca', 'regra': 'Uma marca = um fabricante. Exceção: genérico, separado pela sigla (NIMESULIDA EMS ≠ NIMESULIDA MED).'},
    {'id': 'MAR-02', 'tema': 'marca', 'regra': 'Sigla do fabricante OBRIGATÓRIA no fim da marca de Farmácia, menos dermocosmético.', 'exemplos': ['VITAMINA D3 BIO', 'SOMALIFE ARO', 'DORFLEX OPE']},
    {'id': 'MAR-03', 'tema': 'marca', 'regra': 'Nome do fabricante não entra na marca (ALTHAIA ALT errado → VITAMINA D3 ALT).'},
    {'id': 'MAR-04', 'tema': 'marca', 'regra': 'Item de Farmácia com fabricante conhecido nunca fica OUTRA MARCA: usar nome comercial ou nome do produto.'},
    {'id': 'MAR-05', 'tema': 'marca', 'regra': 'Genérico/produto sem fabricante → "<PRODUTO> OTF", fabricante OUTRO FABRICANTE.', 'exemplos': ['VITAMINA C OTF', 'CURCUMA OTF', 'TRIBULUS TERRESTRIS OTF']},
    {'id': 'MAR-06', 'tema': 'marca', 'regra': 'Marca sem quantidade (54G sai) e nunca palavra de listas.FARMA_NAO_MARCA. POR DEFECTO nunca é marca.'},
    {'id': 'MAR-07', 'tema': 'marca', 'regra': 'Genérico: marca = princípio ativo + sigla do laboratório (LOSARTANA GER).'},
    {'id': 'CAT-01', 'tema': 'categoria', 'regra': 'Toda linha tem EST MER 7 com código ATC no nome oficial (ex.: N02B NAO NARCOTICOS ANTIPIRETICOS).'},
    {'id': 'CAT-02', 'tema': 'categoria', 'regra': 'Ordem: categoria informada/IA → CMED → princípio ativo → vitamina/suplemento → balcão → DIMA.'},
    {'id': 'CAT-03', 'tema': 'categoria', 'regra': 'Suplemento: A-Z ou 3+ nutrientes = MULTIVITAMINICO; 1-2 nutrientes = VITAMINA OUTRO. CALCIO MDK = cálcio + magnésio + D + K.'},
    {'id': 'CAT-04', 'tema': 'categoria', 'regra': 'Item que não é farma vai para a categoria da sua cesta, com alerta.'},
    {'id': 'COD-01', 'tema': 'codigo_interno', 'regra': 'Produtos distintos no mesmo código de barras → CODIGO INTERNO, OUTRA MARCA, OUTRO FABRICANTE + coluna PRODUTOS DISTINTOS NO CODIGO.'},
    {'id': 'DES-01', 'tema': 'descritivo', 'regra': 'Início fixo da categoria (SUPL ALIM [MULT]) ou marca + complemento + dose + quantidade/forma + "(SIGLA)". Máx. 60 caracteres. CPRS = comprimido/drágea, CPS = cápsula.'},
    {'id': 'STA-01', 'tema': 'status', 'regra': 'STATUS: CRIAR MARCA / CRIAR FABRICANTE / CRIAR MARCA E FABRICANTE / SEM FABRICANTE / CRIAR MARCA; SEM FABRICANTE.'},
    {'id': 'COR-01', 'tema': 'correcao', 'regra': 'Ao corrigir arquivo já classificado: mexer só nas linhas com problema; explicar cada ajuste numa coluna AJUSTE.'},
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
                          'CODIGO INTERNO', 'STATUS', 'PRODUTOS DISTINTOS NO CODIGO']},
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
    },
    'fabricantes': C['farmaFabs'],
    'siglas': C['farmaSiglas'],
    'codigosLab': C['farmaCodLab'],
    'marcasHoja': C['farmaMarcas'],
    'marcasDima': C['farmaDima'],
    'principiosAtivos': C['farmaPA'],
    'vitaminas': C['farmaVit'],
    'estMer7': C['estMer7'],
}

for nome, obj in (('farma_regras.json', regras_json), ('farma_dicionarios.json', dic)):
    p = os.path.join(D, nome)
    json.dump(obj, open(p, 'w'), ensure_ascii=False, indent=1)
    print(nome, os.path.getsize(p) // 1024, 'KB')
print('categorias de Farmácia:', len(cats), '| sem código EST MER 7:', sum(1 for e in cats if not e['estMer7']))
