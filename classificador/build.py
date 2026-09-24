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
(here / 'classificador.html').write_text(s, encoding='utf-8')
print('ok:', here / 'classificador.html', f'{len(s):,} bytes')
