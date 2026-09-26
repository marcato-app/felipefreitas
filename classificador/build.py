"""Gera classificador.html a partir de src.html + consts.json.

Uso: python3 build.py
"""
from pathlib import Path

here = Path(__file__).parent
s = (here / 'src.html').read_text(encoding='utf-8')
s = s.replace("claude.use(", "cuse(").replace(
    "const OUT = 'OUTRA CATEGORIA';",
    "const OUT = 'OUTRA CATEGORIA';\nconst cuse = n => (window.claude && typeof window.claude.use === 'function') ? window.claude.use(n) : Promise.resolve(null);",
    1)
s = s.replace('/*CONSTS*/null', (here / 'consts.json').read_text(encoding='utf-8'))
# base de marcas DIMA (dima.py) embutida como gzip em base64
import base64
dz = here / 'dima.json.gz'
s = s.replace('/*DIMA*/null', '"' + base64.b64encode(dz.read_bytes()).decode() + '"' if dz.exists() else 'null')
# lista CMED/Anvisa (cmed.py) embutida do mesmo jeito
cz = here / 'cmed.json.gz'
s = s.replace('/*CMED*/null', '"' + base64.b64encode(cz.read_bytes()).decode() + '"' if cz.exists() else 'null')
(here / 'classificador.html').write_text(s, encoding='utf-8')
print('ok:', here / 'classificador.html', f'{len(s):,} bytes')
# agente de Farmácia: mesmo app, publicado em artifact próprio (link separado do classificador geral)
import json
cf = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
for x in cf['libSeed']['categorias']:
    if x.get('cesta') == 'FARMACIA': x['ativa'] = True  # no agente de Farmácia a cesta já abre ativa
    if x['nome'] in ('PRESERVATIVO', 'ALGODAO', 'OUTROS BEBE PUERICULTURA LEVE'): x['ativa'] = True  # correlatos vendidos em farmácia
f = s.replace((here / 'consts.json').read_text(encoding='utf-8'), json.dumps(cf, ensure_ascii=False), 1)
f = f.replace('<title>Classificador de Backlog</title>', '<title>Classificador Farmácia</title>', 1)
(here / 'farmacia.html').write_text(f, encoding='utf-8')
print('ok:', here / 'farmacia.html')
