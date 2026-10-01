"""Código EST MER 7 (".3.12.1.2.30.3") de cada categoria do app, pela planilha de padrões do cliente
(dados/padroes_descritivo.xlsx: Categoria, Est_mer). Vai para o arquivo baixado, coluna EST MER 7 CODIGO.
Saída: consts.json -> estMer7 = {categoria do app: código}.
Uso: python3 estmer.py && python3 build.py   (depois de nomes_oficiais.py)
"""
import json, re, unicodedata
from pathlib import Path
import openpyxl

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().upper()).split())
sem_cod = lambda s: re.sub(r'^[A-Z]\d\d[A-Z]?\d?\s+', '', N(s))


def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    of = c.get('nomesOficiais', {})
    cod, atc = {}, {}
    for r in list(openpyxl.load_workbook(here / 'dados' / 'padroes_descritivo.xlsx', read_only=True).worksheets[0].iter_rows(values_only=True))[1:]:
        if r[0] and r[1] and re.match(r'^\.?\d+(\.\d+)+$', str(r[1]).strip()):
            cod.setdefault(N(r[0]), str(r[1]).strip()); cod.setdefault(sem_cod(r[0]), str(r[1]).strip())
            a = re.match(r'^([A-Z]\d\d[A-Z]?\d?)\s', N(r[0]) + ' ')
            if a: atc.setdefault(a.group(1), []).append(str(r[1]).strip())  # mesmo código ATC, grafia diferente
    # base de marcas de Farmácia do cliente (Hoja): Est Mer 7 Descripcion + Est Mer Codigo -> completa o que a planilha
    # de padrões não tem (A11C2 VITAMINA D PURA, A11E1 COMPLEXO B PURO...)
    from farma_marcas import ler_linhas
    for pz in sorted((here / 'dados' / 'farma_marcas').glob('*')):
        if pz.suffix.lower() not in ('.tsv', '.csv', '.txt'): continue
        for r in ler_linhas(pz):
            d, k = r.get('EST MER 7 DESCRIPCION', ''), str(r.get('EST MER CODIGO', '')).strip()
            if d and re.match(r'^\.?\d+(\.\d+)+$', k):
                if N(d) not in cod: cod[N(d)] = k
                if sem_cod(d) not in cod: cod[sem_cod(d)] = k
    outros = {n: k for n, k in cod.items() if re.match(r'^[A-Z]\d\d[A-Z]\d\s+(TODOS OS OUTROS|TODAS OUTRAS)', n)}
    out, falta = {}, []
    for x in c['libSeed']['categorias'] + c['cfg']['categorias']:
        nome = x['nome']
        v = cod.get(N(of.get(nome, ''))) or cod.get(N(nome)) or cod.get(sem_cod(of.get(nome, nome)))
        a = re.match(r'^([A-Z]\d\d[A-Z]?\d?)\s', N(of.get(nome, '')) + ' ')
        if not v and a and len(atc.get(a.group(1), [])) == 1: v = atc[a.group(1)][0]
        # grupo pai (A13A) cujo único código no cliente é o "todos os outros" (A13A2 TODOS OS OUTROS TONICOS)
        if not v and a and len(a.group(1)) == 4:
            f = [k for n, k in outros.items() if n.startswith(a.group(1))]
            if len(f) == 1: v = f[0]
        if v: out[nome] = v
        elif x.get('cesta'): falta.append((x.get('cesta'), nome))
    c['estMer7'] = out
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    far = [n for ce, n in falta if ce == 'FARMACIA']
    print(f"{len(out)} categorias com código EST MER 7; sem código: {len(falta)} ({len(far)} de Farmácia)")
    if far: print('  Farmácia sem código:', far)


if __name__ == '__main__':
    main()
