// Extrai do src.html as listas de palavras usadas pelas regras de Farmácia (avaliando as próprias declarações).
const fs = require('fs'), vm = require('vm');
const src = fs.readFileSync(__dirname + '/../src.html', 'utf8');
function stmt(name) {
  const i = src.indexOf('const ' + name + ' =');
  if (i < 0) throw new Error('nao achei ' + name);
  let d = 0, q = null;
  for (let j = i; j < src.length; j++) {
    const ch = src[j];
    if (q) { if (ch === '\\') { j++; continue; } if (ch === q) q = null; continue; }
    if (ch === "'" || ch === '"' || ch === '`') { q = ch; continue; }
    if ('([{'.includes(ch)) d++; else if (')]}'.includes(ch)) d--;
    else if (ch === ';' && d === 0) return src.slice(i, j + 1);
  }
}
const NOMES = ['CONNECT', 'LAB_LIXO', 'LAB_COD_NAO', 'LAB_NOME_NAO', 'SIGLA_SEM_FAB', 'FAB_LIXO', 'FARMA_NAO_MARCA',
  'PALAVRA_DESCRITIVA', 'VIT_NAO', 'PN_FORA', 'TIPO_SAUDE', 'SAIS_DCB', 'UN_CONTA', 'CODIGO_INTERNO'];
// regras em regex (exportadas como texto da regex, para reimplementar no AppGen)
const RX = ['RX_FARMA_ARQ', 'RX_PELE', 'RX_PELE_FORTE', 'RX_NAO_PELE', 'RX_ANTIF_PA', 'ANTIF_OUTRA', 'ANTIF_DERM', 'FORMAS_AP', 'OTC', 'RX_SINAL_FARMA'];
const ctx = { Set, Map, Array, Object };
vm.createContext(ctx);
let code = NOMES.map(stmt).join('\n').replace(/^const /gm, 'var ');
code += "\nPALAVRA_DESCRITIVA.forEach(w => FARMA_NAO_MARCA.add(w));";
vm.runInContext(code, ctx);
const out = {};
for (const n of NOMES) { const v = ctx[n]; out[n] = v instanceof Set ? [...v].filter(Boolean).sort() : v; }
const extra = /const FAB_ALIAS = (\{[^;]*\});/.exec(src); if (extra) out.FAB_ALIAS = vm.runInNewContext('(' + extra[1] + ')');
const rxs = (v) => Object.prototype.toString.call(v) === '[object RegExp]' ? v.source : Array.isArray(v) ? v.map(rxs) : (v && typeof v === 'object') ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, rxs(x)])) : v;
const ctx2 = { Set, Map, Array, Object, RegExp }; vm.createContext(ctx2);
vm.runInContext(RX.map(stmt).join('\n').replace(/^const /gm, 'var '), ctx2);
out.REGEX = Object.fromEntries(RX.map(n => [n, rxs(ctx2[n])]));
fs.writeFileSync(process.argv[2], JSON.stringify(out, null, 1));
console.log(Object.entries(out).map(([k, v]) => k + ':' + (Array.isArray(v) ? v.length : typeof v)).join(' '));
