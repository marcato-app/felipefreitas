"""Converte dados/dicionario_nomenclaturas_farmaceuticas.xlsx em consts.json -> farmaPA.

Cada princípio ativo vira uma regra {pa, partes, cat, validar}:
- partes: lista de termos que TODOS precisam aparecer na descrição (ex.: combinações
  "AMOXICILINA+CLAVULANATO" -> ["AMOXICILINA", "CLAVULANATO"]; "TIMOLOL COLIRIO" -> ["TIMOLOL", "COLIRIO"]).
  Cada termo pode ter sinônimos separados por "|" (ex.: "PARACETAMOL|ACETAMINOFENO").
- cat: categoria da biblioteca (Est Mer 7, ou Est Mer 6 quando o 7 não existe / é "Por Defecto"),
  com o código ATC tirado do nome, igual às categorias de Farmácia da biblioteca.

Uso: python3 farma_pa.py && python3 build.py
"""
import json, re, unicodedata
from pathlib import Path
import openpyxl

here = Path(__file__).parent
XLSX = here / 'dados' / 'dicionario_nomenclaturas_farmaceuticas.xlsx'

def N(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
    return ' '.join(re.sub(r'[^A-Z0-9+/()| ]', ' ', s).split())

# Parênteses que são sinônimo real do princípio ativo (os outros, tipo "(IL 6)", "(OFF LABEL)", são descartados).
SINONIMOS = {'AAS', 'ACETAMINOFENO', 'ALBUTEROL', 'COTRIMOXAZOL', 'MACROGOL', 'COLECALCIFEROL', 'FITOMENADIONA',
             'LISDEXANFETAMINA', 'ESCOPOLAMINA', 'CIANOCOBALAMINA', 'POLIMIXINA E'}
# Forma farmacêutica no nome que vira termo obrigatório.
FORMAS = {'COLIRIO': 'COLIRIO|COL|OFT|OFTALMICO|OFTALMICA|SOL OFT', 'TOPICO': 'CREME|CR|POMADA|POM|GEL|LOCAO|SPRAY|TOPICO|TOPICA|DERM',
          'TOPICA': 'CREME|CR|POMADA|POM|GEL|LOCAO|SPRAY|TOPICO|TOPICA|DERM'}
# Destino do princípio ativo que aparece em mais de uma classe na base (escolha pelo uso mais comum no varejo;
# os que não estão aqui ficam com a primeira linha da planilha).
PRIMARIA = {
    'METOTREXATO': 'ANTIMETABOLITOS', 'SULFASSALAZINA': 'AMINOSALICILATOS INTESTINAIS',
    'ADAPALENO': 'PREPARACOES ANTIACNE TOPICOS', 'ADALIMUMABE': 'MEDICAMENTOS ANTI TNF', 'INFLIXIMABE': 'MEDICAMENTOS ANTI TNF',
    'FINASTERIDA': 'INIBIDORES DA TESTOSTERONA 5 ALFAREDUCTASA SIMPLES', 'DUTASTERIDA': 'INIBIDORES DA TESTOSTERONA 5 ALFAREDUCTASA SIMPLES',
    'ESPIRONOLACTONA': 'AGENTES POUPADORES DE POTASSIO PUROS', 'ACIDO FOLICO': 'OUTROS ANTIANEMICOS INCLUINDO ACIDO FOLICO E FOLIN',
    'CODEINA': 'ANALGESICOS NARCOTICOS', 'HIDROXIDO DE MAGNESIO': 'LAXANTES OSMOTICOS', 'HIDROCORTISONA': 'CORTICOIDES TOPICOS PUROS',
    'DIGOXINA': 'GLICOSIDEOS CARDIACOS PUROS', 'LIRAGLUTIDA': 'AGONISTAS GLP 1', 'SEMAGLUTIDA': 'AGONISTAS GLP 1',
    'ESTREPTOMICINA': 'AMINOGLICOSIDEOS',
}
# Erros evidentes da base (destino que não bate com o princípio ativo, mesmo quando a base marca como "Texto").
# Sobrescrevem a planilha; a coluna "corrigido" do farmaPA marca esses casos. Revisar com o cliente.
CORRECOES = {
    'VITAMINA A': 'VITAMINA A PURA', 'VITAMINA D': 'VITAMINA D PURA', 'VITAMINA K': 'VITAMINA K', 'VITAMINA E': 'VITAMINA OUTRO',
    'CETOROLACO COLIRIO': 'ANTIINFLAMATORIOS OFTALMOLOGICOS NAO ESTEROIDES',
    'LOPINAVIR/RITONAVIR': 'OUTROS ANTIVIRAIS', 'ANFETAMINAS': 'PSICOESTIMULANTES', 'LIDOCAINA': 'ANESTESICOS LOCAIS TOPICOS',
}
# Rótulo de nível 7 que não é igual ao nome da categoria na biblioteca.
ALIAS_CAT = {'TOPICOS': 'TOPICOS OFTALMOLOGICOS ANTIGLAUCOMA', 'ANTIINFLAMATORIO': 'ANTI REUMATICOS NAO ESTEROIDAIS PUROS'}
strip_atc = lambda s: re.sub(r'^[A-Z]\d{2}[A-Z]?\d?\s+', '', N(s))

def partes_de(nome):
    base = N(nome)
    syn = [m.strip() for m in re.findall(r'\(([^)]*)\)', base) if m.strip() in SINONIMOS]
    base = re.sub(r'\([^)]*\)', ' ', base)
    forma = None
    toks = base.split()
    if toks and toks[-1] in FORMAS and len(toks) > 1: forma = FORMAS[toks.pop()]
    comps = [' '.join(p.split()) for p in re.split(r'[+/]', ' '.join(toks)) if p.strip()]
    if len(comps) == 1 and syn: comps = [comps[0] + '|' + '|'.join(syn)]
    return comps + ([forma] if forma else [])

def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    names = {x['nome'] for x in c['libSeed']['categorias']}
    rows = list(openpyxl.load_workbook(XLSX, read_only=True)['Dicionário'].iter_rows(min_row=2, values_only=True))
    por_pa, faltou = {}, []
    for area, classe, sub, pa, e6, e7, cod, fonte in rows:
        if not pa: continue
        alvo = e7 if e7 and N(e7) != 'POR DEFECTO' else e6
        cat = strip_atc(alvo); cat = ALIAS_CAT.get(cat, cat)
        if cat not in names: cat = N(alvo) if N(alvo) in names else None
        if not cat: faltou.append((pa, alvo)); continue
        k = N(re.sub(r'\([^)]*\)', ' ', pa))
        por_pa.setdefault(k, {'pa': str(pa).strip(), 'partes': partes_de(pa), 'cats': [], 'validar': False})
        r = por_pa[k]
        if cat not in r['cats']: r['cats'].append(cat)
        r['validar'] = r['validar'] or 'VALIDAR' in N(fonte or '')
    out = []
    assert all(v in names for v in PRIMARIA.values()), [v for v in PRIMARIA.values() if v not in names]
    for k, r in por_pa.items():
        pri = PRIMARIA.get(k)
        cat = pri if pri in r['cats'] else r['cats'][0]
        cor = CORRECOES.get(k)
        if cor:
            assert cor in names, cor
            if cor != cat: r['cats'].append(cat)
            cat = cor
        out.append({'pa': r['pa'], 'partes': r['partes'], 'cat': cat, 'validar': r['validar'], **({'corrigido': True} if cor else {}),
                    **({'outras': [x for x in r['cats'] if x != cat]} if len(r['cats']) > 1 else {})})
    c['farmaPA'] = out
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    print(f'{len(out)} princípios ativos -> {len({x["cat"] for x in out})} categorias; sem categoria: {faltou}')

if __name__ == '__main__':
    main()
