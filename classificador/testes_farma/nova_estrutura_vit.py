# Distribui os itens de VITAMINA E MINERAL (arquivo Detalhe) na nova estrutura proposta (multivitaminicos_e_vitaminas_Final).
#   python3 testes_farma/nova_estrutura_vit.py <estrutura.xlsx> <Detalhe.csv> <saida.xlsx>
# Ordem: 1) código de barras na CMED -> a classe terapêutica dela (é o mesmo código da estrutura nova);
#        2) produto da CMED pelo nome (marca registrada sem sinal de suplemento);
#        3) regras pelo descritivo (tipo de produto, depois vitaminas/minerais escritos); 4) sem regra -> REVISAR.
import csv, re, sys, unicodedata, collections
import openpyxl
from openpyxl.styles import Font, PatternFill
from pathlib import Path

csv.field_size_limit(10 ** 9)
here = Path(__file__).resolve().parent.parent
EST, DET, OUT = sys.argv[1], sys.argv[2], sys.argv[3]


def N(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().upper()
    s = re.sub(r'(\d),(\d)', r'\1.\2', s)
    return ' '.join(re.sub(r'[^A-Z0-9.+ ]', ' ', s).split())


def cod(x):  # A02A1 -> A2A1 (CMED escreve sem o zero)
    m = re.match(r'^([A-Z])0?(\d+)([A-Z]?)(\d*)', N(x).replace(' ', ''))
    return (m.group(1) + str(int(m.group(2))) + m.group(3) + m.group(4)) if m else ''


# estrutura nova
alvos, por_cod, por_nome = [], {}, {}
for r in list(openpyxl.load_workbook(EST, read_only=True).active.iter_rows(values_only=True))[1:]:
    if not r or not r[3]: continue
    e6 = r[2] or r[3]; e7 = str(r[3]).strip(); a = (str(e6).strip(), e7); alvos.append(a)
    c = cod(e7.split(' - ')[0].split(' ')[0]) if re.match(r'^[A-Z]\d', e7) else ''
    if c: por_cod[c] = a
    por_nome[N(e7)] = a
def alvo(nome):  # por nome da subcategoria sem código (CREATINA, AMINOACIDOS...)
    return por_nome[N(nome)]
def A(c):
    return por_cod[cod(c)]
PADRAO_GRUPO = {}  # classe da CMED fora da estrutura: a subcategoria "outros" do mesmo grupo (A11D1 -> A11D9)
for c, a in por_cod.items():
    g = c[:len(c) - 1] if c[-1].isdigit() and len(c) > 3 else c
    if g not in PADRAO_GRUPO or re.search(r'OUT|TODAS|TOD\.', a[1]): PADRAO_GRUPO[g] = a

# CMED
cm_ean, cm_prod = {}, collections.defaultdict(collections.Counter)
ws = openpyxl.load_workbook(here / 'dados' / 'cmed' / 'cmed_pmc_20260909.xlsx', read_only=True).active
hdr = False
for r in ws.iter_rows(values_only=True):
    if not hdr:
        hdr = bool(r and str(r[0]).startswith('SUBST')); continue
    cl = str(r[10] or '').strip()
    if not cl: continue
    for e in r[5:8]:
        e = re.sub(r'\D', '', str(e or ''))
        if len(e) >= 8: cm_ean[e.lstrip('0')] = (cl, str(r[8] or ''), str(r[11] or ''))
    if r[8]: cm_prod[N(r[8])][cl] += 1


def da_cmed(cl):
    c = cod(cl.split(' - ')[0])
    if c in por_cod: return por_cod[c], 'CMED classe ' + cl
    for k in (c[:-1], c[:4], c[:3]):
        if k in PADRAO_GRUPO: return PADRAO_GRUPO[k], f'CMED classe {cl} (não está na estrutura; usado o grupo)'
    return None, f'CMED classe {cl} (fora da estrutura nova)'


# regras de tipo de produto (ordem importa: a mais específica primeiro)
R = lambda *ws: re.compile(r'(?<![A-Z0-9])(' + '|'.join(re.escape(w).replace('\\ ', ' ') for w in sorted(ws, key=len, reverse=True)) + r')(?![A-Z0-9])')
TIPO = [
    (R('CAFE', 'NESPRESSO', 'CAPSULAS COMPATIVEIS', 'DOLCE GUSTO', 'CAPPUCCINO', 'TIPOIA', 'MUNHEQUEIRA', 'JOELHEIRA', 'TORNOZELEIRA', 'ABSORVENTE', 'ABS INT', 'INJETAVEL', 'SERINGA'), 'FORA'),
    (R('ACETILCISTEINA', 'ACETILZAN', 'NAC', 'LAMBEDOR', 'FINETOSS'), 'R05C0'),
    (R('EMULSAO SCOTT', 'EMULSAOSCOTT', 'OLEO DE FIGADO DE BACALHAU', 'FIGADO DE BACALHAU'), 'A11C3'),
    (R('MASSAGEADOR', 'MASSAGEM', 'BALSAMO', 'ARNICA', 'GEL CRIOTERAPICO', 'COPAIBA', 'SUCURI', 'CANFORA'), 'M02A0'),
    (R('POMADA', 'CREME', 'LOCAO', 'SHAMPOO', 'XAMPU', 'TONICO CAPILAR', 'AMPOLA CAPILAR', 'SERUM', 'TOPICO', 'HIDRATANTE', 'FACIAL', 'PROTETOR SOLAR'), 'D11A'),
    (R('PROPOLIS', 'PROPOLES', 'EXTRATO DE PROPOLIS'), 'EXTRATO DE PROPOLIS'),
    (R('NICOTINA', 'NICORETTE', 'NIQUITIN'), 'N07B0'),
    (R('WHEY', 'PROTEINA', 'PROTEINAS', 'PROTEIN', 'ALBUMINA', 'CASEINA', 'ISOLADA', 'HIPERPROTEICO'), 'V06B0'),
    (R('CREATINA', 'CREATINE', 'CREAPURE'), 'CREATINA'),
    (R('BCAA', 'GLUTAMINA', 'AMINOACIDO', 'AMINOACIDOS', 'LEUCINA', 'ARGININA', 'L ARGININA', 'TAURINA', 'CARNITINA', 'L CARNITINA', 'HMB', 'BETA ALANINA', 'CITRULINA', 'GLICINA', 'TIROSINA', 'L TEANINA', 'TEANINA', 'LISINA', 'METIONINA', 'CISTEINA'), 'AMINOACIDOS'),
    (R('MALTODEXTRINA', 'DEXTROSE', 'CARBOIDRATO', 'PALATINOSE', 'WAXY', 'GEL CARBO', 'CARB UP', 'GEL DE CARBOIDRATO'), 'CARBOIDRATO'),
    (R('PRE TREINO', 'PRE-TREINO', 'PRETREINO', 'POS TREINO', 'PRE WORKOUT', 'PREWORKOUT', 'CAFEINA', 'CAFFEINE', 'HORUS', 'INSANE'), 'PRE TREINO/POS TREINO'),
    (R('SUSTAGEN', 'ENSURE', 'NUTREN', 'FORTINI', 'PEDIASURE', 'GLUCERNA', 'NUTRIDRINK', 'FRESUBIN', 'SUPRA SOY', 'COMPLEMENTO ALIMENTAR', 'COMPLEMENTO NUTRICIONAL', 'NUTREN SENIOR', 'MILNUTRI', 'NOVASOURCE', 'ENSURE', 'SUSTAIN', 'NUTRILON', 'SHAKE'), 'Por Defecto'),
    (R('TERMOGENICO', 'TERMOGENICA', 'EMAGRECEDOR', 'EMAGRECE', 'SECA BARRIGA', 'SLIM', 'DIET', 'DETOX', 'BAIXA BARRIGA', 'QUEIMA', 'LIPO', 'CHITOSAN', 'QUITOSANA', 'CAPSIATE', 'CHA VERDE', 'CHA BRANCO', 'HIBISCO', 'SACIEDADE', 'BERINJELA', 'BERINGELA', 'LARANJA MORO', 'MORO', 'GARCINIA', 'CAMBOGIA', 'SPIRULINA SLIM'), 'V06A0'),
    (R('PROBIOTICO', 'PROBIOTICOS', 'LACTOBACILLUS', 'LACTOBACILOS', 'BIFIDO', 'BIFIDOBACTERIUM', 'BACILLUS', 'SACCHAROMYCES', 'KEFIR', 'YAKULT', 'HILINE', 'SIMFORT', 'FLORATIL', 'ENTEROGERMINA', 'PROBID', 'BILHOES', 'UFC'), 'A07F'),
    (R('FIBRA', 'FIBRAS', 'MUCIL', 'MUCILAGEM', 'METAMUCIL', 'FIBER', 'PSYLLIUM', 'PSILIO', 'PLANTAGO', 'INULINA', 'BENEFIBER', 'FIBERMAIS', 'FIBER MAIS'), 'A06A3'),
    (R('LAXANTE', 'LAXATIVO', 'LACTULOSE', 'SENE', 'CASCARA', 'TAMARINE', 'NATURETTI'), 'A6A2'),
    (R('ENZIMA', 'DIGEST', 'ENZIMAS', 'LACTASE', 'DIGESTIVO', 'DIGESTIVA', 'BROMELINA', 'PAPAINA'), 'A09A0'),
    (R('SIMETICONA', 'LUFTAL', 'ANTIGASES', 'GASES', 'FLATUL'), 'A02A2'),
    (R('ANTIACIDO', 'BICARBONATO', 'AZIA', 'ESTOMAGO', 'ESPINHEIRA SANTA', 'ESPINHEIRA'), 'A02A1'),
    (R('SILIMARINA', 'ALCACHOFRA', 'BOLDO', 'HEPATO', 'HEPATICO', 'FIGADO', 'CARDO MARIANO', 'CARDO'), 'A05B0'),
    (R('SORO', 'HIDRABEN', 'REHIDRABEN', 'RE HIDRABEN', 'HIDRAPLEX', 'ELETROLITO', 'ELETROLITOS', 'REIDRATANTE', 'REIDRATACAO', 'HIDRATACAO ORAL', 'ISOTONICO', 'REPOSITOR'), 'A07G0'),
    (R('MELATONINA'), 'N05B1'),
    (R('VALERIANA', 'PASSIFLORA', 'MARACUJA', 'CAMOMILA', 'MULUNGU', 'ERVA CIDREIRA', 'MELISSA', 'KAVA', 'SONO', 'SLEEP', 'CALMANTE', 'ANSIEDADE', 'ASHWAGANDHA', 'RHODIOLA', 'TRIPTOFANO', 'GABA', '5 HTP', '5HTP'), 'N05B5'),
    (R('GINKGO', 'GINKO', 'MEMORIA', 'MEMORY', 'COGNICAO', 'COLIN', 'MULTICOLIN', 'COGNITIVO', 'FOSFATIDILSERINA', 'BACOPA', 'LECITINA', 'COLINA', 'CEREBRO', 'FOCO'), 'N06D0'),
    (R('GINSENG', 'GUARANA', 'CATUABA', 'MARAPUAMA', 'ENERGIA', 'ENERGETICO', 'ENERGY', 'TONICO', 'FADIGA', 'COMPOSTO ENERGETICO', 'GELEIA REAL'), 'A13A2'),
    (R('APETITE', 'ENGORDA', 'BUCLINA', 'COBAVITAL', 'CIPROEPTADINA'), 'A15A0'),
    (R('CRANBERRY', 'UVA URSI', 'URINARIO', 'URINARIA', 'D MANOSE', 'MANOSE'), 'G04A9'),
    (R('SAW PALMETTO', 'PALMETTO', 'PROSTATA', 'PROSTATICO', 'SEMENTE DE ABOBORA', 'OLEO DE SEMENTE DE ABOBORA', 'PYGEUM'), 'G04C9'),
    (R('LONG JACK', 'TONGKAT', 'TRIBULUS', 'TRIBULLUS', 'MACA PERUANA', 'TESTO', 'TESTOSTERONA', 'LIBIDO', 'VIRILIDADE', 'FENO GREGO', 'FENOGREGO'), 'G04X0'),
    (R('ISOFLAVONA', 'MENOPAUSA', 'AMORA MIURA', 'AMORA', 'CIMICIFUGA', 'ONAGRA', 'PRIMULA', 'BORRAGEM', 'TPM', 'CLIMATERIO', 'INOSITOL', 'MIO INOSITOL', 'FERTILIDADE'), 'G02X9'),
    (R('GLUCOSAMINA', 'CONDROITINA', 'COLAGENO TIPO 2', 'COLAGENO TIPO II', 'COLAGENO II', 'UC II', 'UCII', 'UC-II', 'MSM', 'ARTICULACAO', 'ARTICULACOES', 'ARTICULAR', 'CARTILAGEM', 'CARTIGEN', 'ARTRO', 'ARTROLIVE', 'CONDROFLEX', 'MOBILITY', 'FLEX', 'OSTEO', 'OSSOS'), 'M05X0'),
    (R('CASTANHA DA INDIA', 'CASTANHA DE INDIA', 'CENTELLA', 'CENTELA', 'DIOSMINA', 'HESPERIDINA', 'PINUS PINASTER', 'PYCNOGENOL', 'PICNOGENOL', 'VARIZES', 'PERNAS', 'CIRCULACAO', 'VASCULAR', 'RUTINA'), 'C05C0'),
    (R('COENZIMA', 'COQ 10', 'COQ', 'COENZYME', 'Q10', 'Q 10', 'COQ10', 'UBIQUINOL', 'CARDIO', 'CORACAO'), 'C01X0'),
    (R('OMEGA 3', 'OMEGA3', 'OMEGA 3 6 9', 'OMEGAS', 'OLEO DE PEIXE', 'FISH OIL', 'EPA', 'DHA', 'KRILL', 'OLEO DE LINHACA', 'LINHACA', 'OLEO DE ALHO', 'ALHO', 'FITOESTEROL', 'FITOESTEROIS', 'COLESTEROL', 'CHIA', 'OLEO DE COCO', 'CARTAMO', 'OLEO DE CARTAMO', 'CLA', 'AVESTRUZ', 'OLEO DE PRIMULA', 'OMEGA 369', 'OMEGA', 'TRIPLO OMEGA', 'BIOEPA'), 'C10B0'),
    (R('LUTEINA', 'ZEAXANTINA', 'OCULAR', 'VISAO', 'OLHOS', 'MIRTILO', 'BLUEBERRY'), 'S01M0'),
    (R('EXPECTORANTE', 'FINETOSS', 'TOSS', 'GUACO', 'XAROPE', 'TOSSE', 'GARGANTA', 'PASTILHA', 'AGRIAO', 'MEL E LIMAO'), 'R05C0'),
    (R('CROMO', 'PICOLINATO DE CROMO', 'GLICEMIA', 'DIABETES', 'DIABETICO', 'INSULINA', 'BERBERINA', 'CANELA', 'PATA DE VACA', 'GYMNEMA'), 'A10X9'),
]
COLAGENO = R('COLAGENO HIDROLISADO', 'COLAGENO', 'VERISOL', 'PEPTAN', 'COLLAGEN')
OUTROS_NUTRI = R('CURC', 'CURCUMAX', 'SPIRULINA', 'ESPIRULINA', 'CHLORELLA', 'CLORELA', 'MORINGA', 'CURCUMA', 'ACAFRAO', 'CURCUMINA', 'RESVERATROL', 'ACIDO HIALURONICO', 'HIALURONICO',
                 'POLIFENOIS', 'CAMU CAMU', 'ACEROLA', 'BETERRABA', 'CLOROFILA', 'GELEIA', 'LEVEDO', 'LEVEDURA', 'GERMEN', 'OLEO DE GERMEN', 'ASTAXANTINA', 'LICOPENO',
                 'SUPERFOOD', 'GREENS', 'COGUMELO', 'COGUMELOS', 'GANODERMA', 'CHA', 'ERVA', 'ERVAS', 'EXTRATO', 'COMPOSTO')

# vitaminas e minerais escritos
VIT = {
    'A': R('VITAMINA A', 'VIT A', 'RETINOL', 'BETACAROTENO', 'BETA CAROTENO'),
    'B1': R('B1', 'TIAMINA'), 'B2': R('B2', 'RIBOFLAVINA'), 'B3': R('B3', 'NIACINA', 'NIACINAMIDA', 'NICOTINAMIDA'),
    'B5': R('B5', 'PANTOTENICO'), 'B6': R('B6', 'PIRIDOXINA'), 'B7': R('BIOTINA', 'B7', 'H'), 'B9': R('OFOLATO', 'METILFOLIN', 'ZAFOLAT', 'ACIDO FOLICO', 'FOLATO', 'B9', 'METILFOLATO', 'FOLICO'),
    'B12': R('B12', 'COBALAMINA', 'CIANOCOBALAMINA', 'METILCOBALAMINA', 'HIDROXOCOBALAMINA'),
    'C': R('VITAMINA C', 'VIT C', 'ACIDO ASCORBICO', 'ASCORBATO', 'C 1000', 'C1000', 'C 500', 'C+ZINCO', 'C ZINCO', 'CEBION', 'REDOXON', 'CEWIN', 'TARGIFOR'),
    'D': R('VITAMINA D', 'VIT D', 'D3', 'D2', 'COLECALCIFEROL', 'DEPURA', 'ADDERA'), 'E': R('GERME DE TRIGO', 'VITAMINA E', 'VIT E', 'TOCOFEROL'),
    'K': R('VITAMINA K', 'VIT K', 'K2', 'K1', 'MK7', 'MK 7', 'MENAQUINONA', 'FITOMENADIONA'),
}
COMPLEXO_B = R('COMPLEXO B', 'COMPLEXO VITAMINICO B', 'VITAMINAS DO COMPLEXO B', 'B COMPLEX', 'B-COMPLEX', 'CITONEURIN', 'DEXA CITONEURIN')
MIN = {
    'CALCIO': R('DOLOMITA', 'CALSUPRE', 'CALCIO', 'CA', 'CALCIUM', 'CALTRATE', 'OSCAL', 'OS CAL', 'CALCITRAN'), 'MAGNESIO': R('CAIMBRA', 'CAIMBRAFIM', 'MAGNESIO', 'MAGNESIUM', 'MG DIMALATO', 'DIMALATO', 'TREONATO', 'MAGNESIOS', 'CLORETO DE MAGNESIO', 'MAG'),
    'ZINCO': R('ZINCO', 'ZINC', 'ZN'), 'FERRO': R('ANEMIPLUS', 'FERRO', 'FERROSO', 'FERRICO', 'IRON', 'FE', 'NEUTROFER', 'NORIPURUM', 'COMBIRON'), 'SELENIO': R('SELENIO', 'SELENIUM'),
    'CROMO': R('CROMO'), 'POTASSIO': R('POTASSIO', 'POTASSIUM'), 'IODO': R('IODO', 'IODETO'), 'COBRE': R('COBRE'), 'MANGANES': R('MANGANES'),
}
POLI = R('MULTIMAX', 'A Z', 'AZ', 'A-Z', 'DE A A Z', 'A A Z', 'POLIVITAMINICO', 'POLIVITAMINICOS', 'POLIVIT', 'MULTIVITAMINICO', 'MULTIVITAMINICOS', 'MULTIVIT', 'MULTI VITAMINICO',
         'CENTRUM', 'POLIVITAMINAS', 'MULTIVITAMINAS', 'VITAMINAS E MINERAIS', 'MINERAIS E VITAMINAS', 'SUPRADYN', 'LAVITAN', 'TOTAL', 'MULTI')
GEST = R('MATER', 'GESTANTE', 'GESTANTES', 'GESTACAO', 'PRE NATAL', 'PRENATAL', 'MAMAE', 'MATERNA', 'MATERNIDADE', 'GRAVIDEZ', 'LACTANTE', 'OOGESTA', 'ESTER C GESTANTE')
KIDS = R('KIDS', 'KID', 'INFANTIL', 'CRIANCA', 'CRIANCAS', 'JUNIOR', 'BABY', 'BEBE', 'GOTAS INFANTIL', 'GUMMY KIDS', 'GOMINHAS', 'PEDIATRICO', 'MASTIGAVEL KIDS')
SENIOR = R('SENIOR', 'SENIORX', '50 MAIS', '60 MAIS', '50+', '60+', 'MAIS DE 50', 'TERCEIRA IDADE', 'MELHOR IDADE', 'ACIMA DE 50', 'SILVER')
LINHA = R('SENIOR', 'MULHER', 'HOMEM', 'MEN', 'WOMAN', 'WOMEN', 'KIDS', 'INFANTIL', 'GESTANTE', 'MATER', 'IMUNE', 'IMUNIDADE', 'IMUNO', 'HAIR', 'CABELO', 'CABELOS', 'UNHA', 'UNHAS', 'PELE', 'BEAUTY', 'BELEZA', 'DAY', 'VITAL', 'VITALIDADE', 'GUMMY', 'GOMAS', 'GOMINHAS')
VAGO = R('VITAMINA', 'VITAMINAS', 'VIT')


def classifica(txt, marca, de7=''):
    t = ' ' + txt + ' '
    for rx, c in TIPO:
        if rx.search(t):
            if c == 'FORA': return ('FORA DA ESTRUTURA (nao e vitamina/suplemento)', ''), 'descritivo: ' + rx.search(t).group(1)
            return (A(c) if re.match(r'^[A-Z]\d', c) else alvo(c)), 'descritivo: ' + rx.search(t).group(1)
    v = {k for k, rx in VIT.items() if rx.search(t)}
    if COMPLEXO_B.search(t): v |= {'COMPLEXO B'}
    m = {k for k, rx in MIN.items() if rx.search(t)}
    if 'COMPLEXO B' in v and not POLI.search(t) and not m: return A('A11E1') if 'C' not in v else A('A11E2'), 'complexo B' + (' + C' if 'C' in v else '')
    poli = bool(POLI.search(t)) or len(v - {'COMPLEXO B'}) >= 4 or (len(v) >= 3 and len(m) >= 1)
    if poli:
        # A-Z/polivitamínico comercial tem minerais (Centrum, Lavitan A-Z); sem minerais só quando escrito ou quando são só vitaminas listadas
        mineral = bool(m) or bool(R('MINERAL', 'MINERAIS').search(t)) or (bool(POLI.search(t)) and not R('SEM MINERAIS', 'SO VITAMINAS', 'COMPLEXO VITAMINICO').search(t))
        sub = '1' if GEST.search(t) else '2' if KIDS.search(t) else '3' if (SENIOR.search(t) and mineral) else '4'
        if not mineral and sub == '3': sub = '4'
        return A(('A11A' if mineral else 'A11B') + sub), f"polivitamínico {'com' if mineral else 'sem'} minerais" + {'1': ' (gestante)', '2': ' (infantil)', '3': ' (sênior)', '4': ''}[sub]
    if 'CALCIO' in m: return A('A12A'), 'cálcio' + (' + ' + '+'.join(sorted((v | m) - {'CALCIO'})) if (v | m) - {'CALCIO'} else '')
    if 'FERRO' in m: return (A('B03A1') if not (v | m) - {'FERRO'} else A('B03A2')), 'ferro' + (' + outros' if (v | m) - {'FERRO'} else '')
    if 'POTASSIO' in m and len(m) == 1 and not v: return alvo('A12B - SUPLEMENTOS MINERAIS Á BASE DE POTÁSSIO'), 'potássio'
    if 'C' in v:
        return (A('A11G1') if not (v | m) - {'C'} else A('A11G2')), 'vitamina C' + (' + ' + '+'.join(sorted((v | m) - {'C'})) if (v | m) - {'C'} else '')
    if 'MAGNESIO' in m and not v: return A('A12C1'), 'magnésio' + (' + ' + '+'.join(sorted(m - {'MAGNESIO'})) if m - {'MAGNESIO'} else '')
    if 'COMPLEXO B' in v:
        return (A('A11E1') if not (v | m) - {'COMPLEXO B', 'B1', 'B2', 'B3', 'B5', 'B6', 'B7', 'B9', 'B12'} else A('A11E3')), 'complexo B'
    bs = v & {'B1', 'B6', 'B12'}
    if 'B1' in v and v <= {'B1', 'B6', 'B12'} and not m: return (A('A11D3') if v == {'B1'} else A('A11D4')), '+'.join(sorted(v))
    if v == {'B12'} and not m: return A('A11F'), 'vitamina B12'
    if v == {'B6'} and not m: return A('A11X2'), 'vitamina B6'
    if v == {'E'} and not m: return A('A11X3'), 'vitamina E'
    if v == {'A'} and not m: return A('A11C1'), 'vitamina A'
    if v == {'A', 'D'} and not m: return A('A11C3'), 'vitaminas A+D'
    if 'D' in v and v <= {'D', 'K'} and not m: return A('A11C2'), 'vitamina D' + (' + K2' if 'K' in v else '')
    if v == {'K'} and not m: return A('B02B1'), 'vitamina K'
    if v == {'B9'} and not m: return A('B03X'), 'ácido fólico'
    if m and not v: return (A('A12C1') if m == {'MAGNESIO'} else A('A12C2')), 'minerais: ' + '+'.join(sorted(m))
    if v: return A('A11X9'), 'outras vitaminas: ' + '+'.join(sorted(v | m))
    if COLAGENO.search(t): return A('V06D0'), 'colágeno'
    if de7 == 'MULTIVITAMINICO' or LINHA.search(t):  # linha de polivitamínico sem composição escrita (CRONOVIT SENIOR, MEGA MULHER, IMECAP HAIR)
        sub = '1' if GEST.search(t) else '2' if KIDS.search(t) else '3' if SENIOR.search(t) else '4'
        return A('A11A' + sub), 'POLI_LINHA'
    if OUTROS_NUTRI.search(t): return A('V06D0'), 'outro nutriente: ' + OUTROS_NUTRI.search(t).group(1)
    return None, 'sem regra'


rd = csv.reader(open(DET, encoding='utf-16'), delimiter='\t'); h = next(rd)
res, cnt, cnt_de = [], collections.Counter(), collections.Counter()
for r in rd:
    if len(r) < 50 or not r[2].strip(): continue
    bc = r[2].strip(); desc, top, mx, marca, fab, de7 = r[3], r[47], r[49], r[19], r[21], r[17]
    txt = N(' '.join([desc, top, mx]))
    a, como, conf = None, '', ''
    e = cm_ean.get(re.sub(r'\D', '', bc).lstrip('0'))
    if e:
        a, como = da_cmed(e[0]); conf = 'ALTA (registro CMED)'
        if a is None: conf = 'REVISAR'
    if a is None:
        a2, como2 = classifica(txt, marca, de7)
        if a2: a, como, conf = a2, (como + ' | ' if como else '') + como2, 'MEDIA (regra do descritivo)'
        if como2 == 'POLI_LINHA': como, conf = (como.replace('POLI_LINHA', 'polivitamínico pela linha do produto (composição não escrita; minerais presumidos)')), 'BAIXA (conferir composição)'
    if a is None:
        a, como, conf = (A('V06D0'), (como + ' | ' if como else '') + 'nenhuma regra: sugerido OUT NUTRIENTES', 'REVISAR')
    if False and re.search(r'(VITAMINA C|vitamina C|polivit|complexo B)', como) is None and VAGO.search(' ' + txt + ' ') is None and not re.search(r'descritivo|colágeno|outro nutriente|minerais|cálcio|ferro|magnésio|potássio|vitamina|B1|B6|B12', como):
        conf = 'BAIXA'
    res.append([int(bc) if bc.isdigit() and len(bc) <= 15 else bc, desc, top, marca, fab, de7, a[0], a[1], como, conf, float(str(r[40]).replace('.', '').replace(',', '.') or 0) if r[40] else 0])
    cnt[a] += 1; cnt_de[(de7, a)] += 1

wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'ITENS'
cab = ['CODIGO BARRAS', 'DESCRICAO', 'DESCRICAO LOJA (TOP)', 'MARCA', 'FABRICANTE', 'EST MER 7 ATUAL', 'NOVA EST MER 6', 'NOVA EST MER 7', 'COMO FOI DECIDIDO', 'CONFIANCA', 'VENDA 24M']
ws.append(cab)
cor = {'ALTA': 'C6EFCE', 'MEDIA': 'FFF2CC', 'BAIXA': 'F8CBAD', 'REVISAR': 'FFC7CE'}
for x in sorted(res, key=lambda x: (x[9].startswith('REVISAR'), x[6], x[7], -x[10])):
    ws.append(x); c = ws.cell(ws.max_row, 10); c.fill = PatternFill('solid', fgColor=cor[x[9].split(' ')[0]])
for c in ws[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F3864')
for col, w in zip('ABCDEFGHIJK', [15, 50, 45, 24, 28, 18, 42, 40, 50, 24, 12]): ws.column_dimensions[col].width = w
ws.freeze_panes = 'A2'; ws.auto_filter.ref = ws.dimensions; ws.column_dimensions['K'].number_format = '#,##0'

w2 = wb.create_sheet('RESUMO', 0)
w2.append(['NOVA EST MER 6', 'NOVA EST MER 7', 'ITENS', 'VINDOS DE VITAMINA OUTRO', 'VINDOS DE MULTIVITAMINICO', 'VENDA 24M'])
venda = collections.Counter()
for x in res: venda[(x[6], x[7])] += x[10]
for a in alvos + [('FORA DA ESTRUTURA (nao e vitamina/suplemento)', '')]:
    w2.append([a[0] or '(sem regra - revisar)', a[1], cnt[a], cnt_de[('VITAMINA OUTRO', a)], cnt_de[('MULTIVITAMINICO', a)], round(venda[a])])
w2.append([]); w2.append(['TOTAL', '', len(res)])
conf = collections.Counter(x[9].split(' ')[0] for x in res)
w2.append([]); w2.append(['CONFIANCA', 'ITENS'])
for k in ('ALTA', 'MEDIA', 'BAIXA', 'REVISAR'): w2.append([k, conf[k]])
for c in w2[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F3864')
for col, w in zip('ABCDEF', [52, 58, 10, 22, 24, 16]): w2.column_dimensions[col].width = w
w2.freeze_panes = 'A2'
w3 = wb.create_sheet('COMO LER')
for l in ['Cada item de VITAMINA E MINERAL do Detalhe foi colocado numa subcategoria da estrutura nova (Planilha2).',
          'ALTA: o código de barras está na lista CMED (Anvisa); a classe terapêutica dela é o mesmo código da estrutura nova.',
          'MEDIA: regra pelo descritivo - tipo de produto (probiótico, ômega 3, colágeno tipo 2, creatina...) ou as vitaminas/minerais escritos',
          '   (A-Z ou 4+ vitaminas = polivitamínico; só vitamina D = A11C2; cálcio = A12A; magnésio = A12C1; C = A11G1/A11G2...).',
          'BAIXA / REVISAR: sem regra segura - conferir.',
          'Aba RESUMO: quantos itens iriam para cada subcategoria nova (inclusive as que ficariam vazias).']:
    w3.append([l])
w3.column_dimensions['A'].width = 140
wb.save(OUT)
print(len(res), dict(conf))
print(cnt.most_common(45))
