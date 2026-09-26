"""Compara a saída do app (rodar_vit.js) com a base do cliente de VITAMINA E MINERAL."""
import csv, json, re, sys, collections
from pathlib import Path
here = Path(__file__).parent
base = list(csv.DictReader(open(here.parent / 'dados' / 'vitaminas' / 'vitamina_mineral.tsv', encoding='utf-8'), delimiter='\t'))
out = json.load(open(sys.argv[1] if len(sys.argv) > 1 else here / 'vitaminas_saida.json'))
N = lambda s: re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]', ' ', str(s or '').upper())).strip()
c = collections.Counter(); cats = collections.Counter(); ex = collections.defaultdict(list)
for b, (bc, d, cat, marca, fab, desc, qt, *resto) in zip(base, out):
    reg = bool(resto and resto[0])
    e7 = b['Est Mer 7 Descripcion']; c['n'] += 1
    ok_cat = N(cat).endswith(N(e7)); c['cat'] += ok_cat; cats[(e7, cat)] += 1
    if reg and not ok_cat: c['reg'] += 1; ex['remedio registrado (categoria de remedio)'].append((d, e7, cat))
    elif not ok_cat: ex['cat'].append((d, e7, cat))
    ini = 'SUPL ALIM MULT' if e7 == 'MULTIVITAMINICO' else 'SUPL ALIM'
    ok_ini = desc.startswith(ini + ' ') and (e7 == 'MULTIVITAMINICO' or not desc.startswith('SUPL ALIM MULT'))
    c['inicio'] += ok_ini or (reg and not ok_cat)  # remédio registrado segue o padrão FARMA (marca/princípio ativo)
    m = N(b['Marca']); m0 = m.rsplit(' ', 1)[0] if len(m.split()) > 1 else m
    if m not in ('OUTRA MARCA', 'POR DEFECTO', ''):
        c['n_marca'] += 1; ok = N(marca) in (m, m0) or N(marca).startswith(m0); c['marca'] += ok
        if not ok: ex['marca'].append((d, b['Marca'], marca))
    if b['Fabricante'] not in ('OUTRO FABRICANTE', 'SIN PROVEEDOR ASOCIADO', ''):
        c['n_fab'] += 1; c['fab'] += N(fab) == N(b['Fabricante'])
    try: q = float(b['Contenido'])
    except ValueError: q = 0
    if q > 1:
        c['n_qt'] += 1; ok = abs((qt or 0) - q) < 0.01; c['qt'] += ok
        if not ok: ex['qt'].append((d, q, qt))
pct = lambda a, n: f"{c[a]}/{c[n]} ({100 * c[a] / max(1, c[n]):.0f}%)"
print(f"{c['n']} itens | EST MER 7 certa {pct('cat', 'n')} (+ {c['reg']} remédios registrados na categoria de remédio) | começa com o padrão {pct('inicio', 'n')} | marca {pct('marca', 'n_marca')} | "
      f"fabricante {pct('fab', 'n_fab')} | conteúdo {pct('qt', 'n_qt')}")
print('categorias do app:', cats.most_common(12))
with open(here / 'vitaminas_erros.txt', 'w', encoding='utf-8') as f:
    for k, v in ex.items():
        f.write(f'== {k} ({len(v)})\n' + ''.join(' | '.join(map(str, x)) + '\n' for x in v[:400]))
