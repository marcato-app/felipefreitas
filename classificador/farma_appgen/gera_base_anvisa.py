"""farma_base_anvisa.json (AppGen) a partir do cmed.json.gz: código de barras -> [produto, apresentação, laboratório,
classe CMED, substância, tipo, origem] + registrados sem código de barras.
Uso: python3 cmed.py && python3 farma_appgen/gera_base_anvisa.py
"""
import datetime, gzip, json, os
D = os.path.dirname(os.path.abspath(__file__))
d = json.loads(gzip.decompress(open(os.path.join(D, '..', 'cmed.json.gz'), 'rb').read()))
antigo = json.load(open(os.path.join(D, 'farma_base_anvisa.json'))) if os.path.exists(os.path.join(D, 'farma_base_anvisa.json')) else {}
eans = {}
for r in d['rows']:
    org = r[7] if len(r) > 7 else 'ATUAL'
    v = [d['prod'][r[1]], r[2], d['lab'][r[3]], d['cls'][r[4]], d['sub'][r[5]], d['tipo'][r[6]], org]
    for e in r[0].split(','): eans.setdefault(e, v)
fmt = antigo.get('formato', {})
fmt['origem'] = '"ATUAL" = lista PMC da CMED atual; "AAAAMMDD" = só nessa edição antiga da CMED; "ABERTOS" = dados abertos de preços da Anvisa (classe pelo nome do produto nas listas PMC; senão pela substância quando ela tem uma classe dominante; vazia quando não dá para saber, ex. fitoterápico NC/NI)'
out = {'versao': datetime.date.today().isoformat(), 'fonte': d['fonte'], 'formato': fmt, 'eans': eans, 'registrados': antigo.get('registrados', d.get('reg', []))}
json.dump(out, open(os.path.join(D, 'farma_base_anvisa.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(eans), 'códigos;', os.path.getsize(os.path.join(D, 'farma_base_anvisa.json')) // 1024, 'KB')
