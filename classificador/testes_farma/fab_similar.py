# Compara uma lista de fabricantes novos com o Hoja (e DIMA/farmaFabs) e aponta parecidos.
import csv, json, re, sys, unicodedata, difflib, collections, openpyxl
S='/tmp/claude-0/-home-user-felipefreitas/7443e5f8-7000-5ee7-ae7b-4c71ad3bdb8e/scratchpad'
LIXO=set('LTDA LTD SA S A EIRELI ME EPP IND INDUSTRIA INDUSTRIAL COM COMERCIO COMERCIAL DE DO DA DOS DAS E LAB LABORATORIO LABORATORIOS LABS FARMACEUTICA FARMACEUTICO FARMACEUTICOS PRODUTOS PRODUTO CIA IMP EXP IMPORTACAO EXPORTACAO DISTRIBUIDORA DIST BRASIL BR DO BRASIL GROUP GRUPO INC CO LLC THE'.split())
def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode().upper()
    return re.sub(r'[^A-Z0-9 ]',' ',s).split()
def core(s): w=[x for x in norm(s) if x not in LIXO]; return ' '.join(w) or ' '.join(norm(s))
r=list(csv.reader(open(S+'/hoja46/Hoja 1 (46).csv',encoding='utf-16'),delimiter='\t'))
info=collections.defaultdict(lambda:[0,collections.Counter(),collections.Counter()])
for x in r[1:]:
    if not x or not x[0].strip(): continue
    f=x[0].strip(); i=info[f]
    try: i[0]+=int(x[8] or 0)
    except: pass
    i[1][x[1].strip()]+=1; i[2][x[3].strip()]+=1
fabs=[f for f in info if f not in ('OUTRO FABRICANTE','POR DEFECTO')]
idx=collections.defaultdict(list); first=collections.defaultdict(list)
for f in fabs:
    c=core(f); idx[c].append(f)
    for w in c.split(): first[w].append(f)
cores={f:core(f) for f in fabs}
def busca(n):
    c=core(n); out=[]
    if n.strip().upper() in info: return [('JA EXISTE (igual)',n.strip().upper())]
    for f in idx.get(c,[]): out.append(('MESMO NOME (sem LTDA/LAB etc.)',f))
    ws=c.split()
    cand=set()
    for w in ws:
        if len(w)>=4: cand.update(first.get(w,[]))
    for f in cand:
        if f in [o[1] for o in out]: continue
        fc=cores[f]; fw=fc.split()
        if fc and (fc.startswith(c+' ') or c.startswith(fc+' ')) : out.append(('UM CONTEM O OUTRO',f))
        elif ws and fw and ws[0]==fw[0] and len(ws[0])>=5: out.append(('MESMA 1a PALAVRA',f))
    # parecido na escrita (erro de digitação)
    near=difflib.get_close_matches(c,[cores[f] for f in fabs if abs(len(cores[f])-len(c))<=3],n=5,cutoff=0.86)
    for nc in near:
        for f in idx[nc]:
            if f not in [o[1] for o in out]: out.append(('ESCRITA PARECIDA',f))
    return out
if __name__=='__main__':
    lista=[l.strip() for l in open(sys.argv[1]) if l.strip()]
    wb=openpyxl.Workbook(); w=wb.active; w.title='COMPARACAO'
    w.append(['FABRICANTE NOVO','RESULTADO','PARECIDO NO HOJA','TIPO','QTD SKU HOJA','MARCAS NO HOJA','CATEGORIAS NO HOJA'])
    cnt=collections.Counter()
    for n in lista:
        res=busca(n)
        if not res: w.append([n,'PODE CRIAR','','','','','']); cnt['PODE CRIAR']+=1; continue
        tag='JA EXISTE' if res[0][0].startswith('JA') else 'VERIFICAR'
        cnt[tag]+=1
        for t,f in res[:6]:
            i=info[f]; w.append([n,tag,f,t,i[0],', '.join(m for m,_ in i[1].most_common(5)),', '.join(m for m,_ in i[2].most_common(3))])
    wb.save(sys.argv[2]); print(cnt)
