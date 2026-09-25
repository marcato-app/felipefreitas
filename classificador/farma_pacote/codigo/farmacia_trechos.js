// Trechos de Farmácia extraídos de classificador/src.html (app completo: classificador.html).
// Não roda sozinho: depende de N(), escRx(), GENERIC, data.dict/data.dima etc. do app.

// ======================================================================
// Abreviações de forma farmacêutica (descritivo)
// ======================================================================
// Farmácia: abreviações de forma farmacêutica (COMP é comprimido, não "composto")GROUP_TOK.FARMA = Object.assign({ COMP: 'COMPRIMIDO', COMPR: 'COMPRIMIDO', CP: 'COMPRIMIDO', CPR: 'COMPRIMIDO', CPS: 'COMPRIMIDO', CAP: 'CAPSULA', CAPS: 'CAPSULA',
  DRG: 'DRAGEA', SOL: 'SOLUCAO', SUSP: 'SUSPENSAO', XPE: 'XAROPE', XAR: 'XAROPE', GTS: 'GOTAS', POM: 'POMADA', AMP: 'AMPOLA', INJ: 'INJETAVEL', EFERV: 'EFERVESCENTE', REV: 'REVESTIDO' }, GROUP_TOK.FARMA || {});

// ======================================================================
// Formas farmacêuticas contam como unidade (conteúdo)
// ======================================================================
const RX_UN = /(?<![0-9.A-Z])(\d{1,3})\s*(?:UN|UND|UNID|UNIDADE|UNIDADES|UNI|UNDS|UNS|UNDS|COMP|COMPR|COMPRIMIDO|COMPRIMIDOS|CP|CPR|CPS|CAP|CAPS|CAPSULA|CAPSULAS|DRG|DRAGEA|DRAGEAS|FOLHASCONT)(?![A-Z])/g;

// ======================================================================
// Categoria pelo princípio ativo
// ======================================================================
const RX_PET = /(?<![A-Z0-9])(?:PET|PETS|CAO|CAES|CACHORRO|CACHORROS|GATO|GATOS|CANINO|CANINOS|FELINO|FELINOS|VET|VETERINARIO|VETERINARIA|EQUINO|BOVINO|AVES)(?![A-Z0-9])/;
function compilePA(active) {
  const rules = (K.farmaPA || []).filter(r => active.has(r.cat)).map(r => ({ ...r, alts: r.partes.map(p => p.split('|').map(N).filter(Boolean)) }));
  if (!rules.length) return null;
  const idx = new Map();
  rules.forEach((r, i) => r.alts.forEach(a => a.forEach(x => { if (!idx.has(x)) idx.set(x, new Set()); idx.get(x).add(i); })));
  const terms = [...idx.keys()].sort((a, b) => b.length - a.length);
  return { rules, idx, rx: new RegExp('(?<![A-Z0-9])(?:' + terms.map(escRx).join('|') + ')(?![A-Z0-9])', 'g') };
}
function matchPA(t, P) {
  if (!P || !t) return null;
  const pos = new Map(); let m; P.rx.lastIndex = 0;
  while ((m = P.rx.exec(t))) if (!pos.has(m[0])) pos.set(m[0], m.index);
  if (!pos.size) return null;
  const cand = new Set(); for (const x of pos.keys()) for (const i of P.idx.get(x)) cand.add(i);
  let best = null, bk = null;
  for (const i of cand) {
    const r = P.rules[i]; let first = Infinity, ok = true;
    for (const a of r.alts) { const ps = a.filter(x => pos.has(x)).map(x => pos.get(x)); if (!ps.length) { ok = false; break; } first = Math.min(first, Math.min(...ps)); }
    if (!ok) continue;
    // mais partes (combinação/forma) ganha; empate: o princípio que aparece primeiro na descrição
    const k = [r.alts.length, -first];
    if (!bk || k[0] > bk[0] || (k[0] === bk[0] && k[1] > bk[1])) { best = r; bk = k; }
  }
  return best;
}
// termo do princípio ativo como aparece na descrição (ex.: "PARACETAMOL", e não "PARACETAMOL (ACETAMINOFENO)")
function paIni(r, T) { const a = r.alts[0]; for (const t of T) for (const x of a) if (new RegExp('(?<![A-Z0-9])' + escRx(x) + '(?![A-Z0-9])').test(t)) return x; return a[0]; }
function classifyDesc(t, C) {
  const r = classifyRules(t, C);
  if (r === OUT && C.sempre && C.sempre.test(t)) return r;
  // princípio ativo decide dentro de Farmácia (e ganha da cesta PET quando a descrição não fala de animal);
  // categoria de outra cesta que bateu pelas regras (shampoo com cetoconazol, bicarbonato culinário) continua valendo
  if (C.pa && (!r || C.cesta.get(r) === 'FARMACIA' || (C.cesta.get(r) === 'PET' && !RX_PET.test(t)))) { const p = matchPA(t, C.pa); if (p) return p.cat; }
  return r;
}

// ======================================================================
// Fabricante = laboratório da descrição
// ======================================================================
/* ---- Farmácia: fabricante é sempre o laboratório escrito na descrição, conferido com o dicionário / DIMA ---- */
const ATC_RX = /^[A-Z]\d\d[A-Z]?\d? /;
const LAB_LIXO = new Set('LABORATORIO LABORATORIOS LAB LABS FARMACEUTICA FARMACEUTICOS FARMACEUTICO FARMA PHARMA PHARMACEUTICA IND INDUSTRIA COM COMERCIO SA S A LTDA ME EIRELI DO DA DE E BRASIL BR'.split(' '));
const LAB_COD_NAO = new Set('MARCA OUTRA OUTRO COM SEM CPR COMP CAP CAPS DRG GTS SOL SUS XPE AMP INJ CRE POM GEL ADT INF PED UN UND CX FR'.split(' '));
// nome do laboratório como aparece na descrição -> código de 3 letras da base (o fabricante vem do código)
const LAB_ALIAS = { GERMED: 'GER', LEGRAND: 'LEG', 'NEO QUIMICA': 'NEO', NEOQUIMICA: 'NEO', 'NOVA QUIMICA': 'NVQ', NOVAQUIMICA: 'NVQ',
  PRATI: 'PRD', 'PRATI DONADUZZI': 'PRD', SANOFI: 'SNF', MULTILAB: 'MUL', MANTECORP: 'MAN', KLEY: 'KLE', 'KLEY HERTZ': 'KLE' };
let LABS = null;
function labIndex() {
  if (LABS) return LABS;
  const nomes = new Map(), cod = new Map();
  for (const DD of [data.dict, data.dima].filter(Boolean)) for (const [mn, b] of DD.map) {
    for (const [em, fm] of b.fabEm) { if (!ATC_RX.test(em + ' ')) continue;
      let f = null, v = -1; for (const [ff, vv] of fm) if (ff !== 'OUTRO FABRICANTE' && vv > v) { v = vv; f = ff; } if (!f) continue;
      const k = N(f); if (!nomes.has(k)) nomes.set(k, f); // o dicionário vem primeiro: grafia dele ganha
      const w = mn.split(' '); const last = w[w.length - 1];
      if (w.length >= 2 && /^[A-Z0-9]{2,4}$/.test(last) && !LAB_COD_NAO.has(last)) { if (!cod.has(last)) cod.set(last, new Map()); cod.get(last).set(f, (cod.get(last).get(f) || 0) + 1); } }
  }
  const codigo = new Map(); for (const [c, m] of cod) { let tot = 0, f = null, v = 0; for (const [ff, vv] of m) { tot += vv; if (vv > v) { v = vv; f = ff; } } if (tot >= 3 && v / tot >= 0.8) codigo.set(c, f); }
  const chave = new Map(); // termo que pode aparecer em qualquer lugar da descrição -> fabricante
  for (const [k, f] of nomes) { const w = k.split(' ').filter(x => !LAB_LIXO.has(x)); if (!w.length) continue;
    const full = w.join(' '); if (full.length >= 3 && !GENERIC.has(full)) chave.set(full, f); } // nome completo (sem LTDA, FARMA...), nunca só a 1ª palavra
  for (const [a, c] of Object.entries(LAB_ALIAS)) if (codigo.has(c)) chave.set(a, codigo.get(c));
  const termos = [...chave.keys()].sort((a, b) => b.length - a.length);
  LABS = { chave, codigo, rx: termos.length ? new RegExp('(?<![A-Z0-9])(?:' + termos.map(escRx).join('|') + ')(?![A-Z0-9])') : null };
  return LABS;
}
function labDaDescricao(T) {
  const L = labIndex();
  for (const t of T) { // 1ª descrição primeiro
    const m = L.rx && t.match(L.rx); if (m) return L.chave.get(m[0]);
    const w = t.split(' '); const last = w[w.length - 1]; if (L.codigo.has(last)) return L.codigo.get(last);
  }
  return null;
}

// ======================================================================
// No runAll (por item): descritivo, fabricante, alertas
// ======================================================================
const conhecidos = b ? new Set([...b.fabAll.keys()].filter(f => f !== 'OUTRO FABRICANTE').map(N)) : new Set();
      if (fs && (!conhecidos.size || conhecidos.has(N(fs)) || (cc && cc.cesta === 'FARMACIA'))) fab = fs; // Farmácia: fabricante pelo laboratório, logo abaixo
      else if (fs) { fab = fabricante(sm, seg, BD); arqAl.push(`Arquivo: fabricante ${fs} não é de ${marca} na base; usado ${fab}`); }
      else fab = b ? fabricante(sm, seg, BD) : 'OUTRO FABRICANTE';
    } else {
      if (!marcaArq) for (const DD of brandDicts()) { bn = findBrand(T, seg, it.sugMarca, C.black, DD, vocab); if (bn) { BD = DD; break; } }
    // ...
    }
    if (cc && cc.cesta === 'FARMACIA') { // fabricante = laboratório da descrição
      const lab = labDaDescricao(T);
      if (lab) {
        if (prioArq() && valido(it.sugFab) && N(it.sugFab) !== N(lab)) arqAl.push(`Arquivo: fabricante ${it.sugFab.trim()} difere do laboratório na descrição (${lab}); usado ${lab}`);
        fab = lab;
    // ...
      }
    // ...
    // Farmácia sem início fixo no manual: começa pela marca; sem marca, pelo princípio ativo (ou pelo nome do produto)
    const farmaLivre = cc && cc.cesta === 'FARMACIA' && !cc.inicio;
    const paHit = farmaLivre && !bn && C.pa ? T.map(t => matchPA(t, C.pa)).find(Boolean) : null;
    const ini = farmaLivre ? (bn ? '' : paHit ? paIni(paHit, T) : nounOutra(T, bn))
      : (cc && cc.dinamico) ? (tipoIni(T, a.per, a.cat, C) || nounOutra(T, bn)) : a.cat === OUT ? nounOutra(T, bn) : (cc.inicio || cc.nome);
    const keepT = T.filter((t, j) => a.per[j] === a.cat); const T2 = keepT.length ? keepT : T;
    // ...
    const brandTxt = bn ? cleanD(marca) : '';
    // ...
    const comp = complement(T2, a.cat, ini, bn || '', groupOf(a.cat), cc);
    // ...
    { const C0 = C.pa && T.map(t => matchPA(t, C.pa)).find(p => p && p.cat === a.cat);
      if (C0) alerts.push('Categoria pelo princípio ativo ' + C0.pa + (C0.corrigido ? ' (destino corrigido em relação à base)' : C0.validar ? ' (base pede validação)' : '')); }
    if (a.arqTrocada) alerts.push(`Arquivo: categoria ${a.arqTrocada} não bate com a descrição (outra cesta); usada ${a.cat}`);
    alerts.push(...arqAl);
    if (a.misturadas) alerts.push(`Descrições de produtos diferentes no mesmo código (${a.misturadas} ignorada${a.misturadas > 1 ? 's' : ''})`);
    if (a.flag === 'SEM_EVIDENCIA') alerts.push('Nenhuma categoria reconhecida na descrição');
    // ...
    else if (q.flag === 'QTD_DIV') alerts.push('Quantidades diferentes entre descrições');
    const pri = alerts.some(x => /^(Nenhuma|Descrições|Sem evidência|Arquivo: categoria)/.test(x)) ? 1 : alerts.some(x => !x.startsWith('Categoria pelo princípio ativo') || /\((base pede validação|destino corrigido em relação à base)\)$/.test(x)) ? 2 : 0;
    res.push({ it, cat: a.cat, marca, fab, qt: q.tot, qbase: q.base, desc, alerts, pri });
    if (i % 250 === 0) { $('#prog').style.width = (100 * i / items.length).toFixed(1) + '%'; $('#runState').textContent = `Classificando ${i.toLocaleString('pt-BR')} de ${items.length.toLocaleString('pt-BR')}…`; await new Promise(r => setTimeout(r, 0)); }
  }

    // ...

// ======================================================================
// Farmácia fica fora da regra "marca tem que existir na EST MER 6"
// ======================================================================
// Farmácia tem regra própria (fabricante): fica como antes, sem ligação EST MER 6 obrigatória
  const farma = cat => { const cc = byName.get(cat); return !!cc && cc.cesta === 'FARMACIA'; };

