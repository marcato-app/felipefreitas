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
const ctx = { Set, Map, Array, Object };
vm.createContext(ctx);
let code = NOMES.map(stmt).join('\n').replace(/^const /gm, 'var ');
code += "\nPALAVRA_DESCRITIVA.forEach(w => FARMA_NAO_MARCA.add(w));";
vm.runInContext(code, ctx);
const out = {};
for (const n of NOMES) { const v = ctx[n]; out[n] = v instanceof Set ? [...v].filter(Boolean).sort() : v; }
const extra = /const FAB_ALIAS = (\{[^;]*\});/.exec(src); if (extra) out.FAB_ALIAS = vm.runInNewContext('(' + extra[1] + ')');
fs.writeFileSync(process.argv[2], JSON.stringify(out, null, 1));
console.log(Object.entries(out).map(([k, v]) => k + ':' + (Array.isArray(v) ? v.length : typeof v)).join(' '));
