// Confere marca/fabricante de Farmácia contra dados/farma_marcas_fabricantes.tsv (Hoja 1 46, marca x fabricante).
// Genérico (nome com princípio ativo): marca = princípio ativo, fabricante = laboratório; senão: marca = nome comercial.
// Uso: NODE_PATH=$(npm root -g) node testes_farma/rodar_hoja.js
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, '..');
const exp = fs.readFileSync(path.join(__dirname, 'hoja_marcas_esperado.tsv'), 'utf8').trim().split('\n').map(l => l.split('\t'));
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  p.on('pageerror', e => console.error('ERRO', e.message));
  await p.setContent(require('fs').readFileSync(path.join(dir, 'classificador.html'), 'utf8'), { waitUntil: 'load', timeout: 120000 }); // a página não declara charset (o artifact recebe do serviço)
  await p.waitForFunction(() => typeof data !== 'undefined' && data.dima, null, { timeout: 60000 });
  await p.evaluate(() => { for (const c of cfg.categorias) c.ativa = true; renderCats(); });
  await p.setInputFiles('#fBacklog', path.join(__dirname, 'hoja_marcas.csv'));
  await p.waitForFunction(() => !document.querySelector('#btnRun').disabled, null, { timeout: 60000 });
  await p.evaluate(() => { if (typeof irEtapa === 'function') irEtapa(6); }); await p.click('#btnRun');
  await p.waitForFunction(() => data.results && data.results.length, null, { timeout: 300000 });
  const r = await p.evaluate(exp => { const C = compile(); const m = new Map(data.results.map(x => [String(x.it.barcode), x]));
    return exp.map(([bc, mar, base, cod, fab]) => { const x = m.get(bc); const pa = C.pa && matchPA(N(base), C.pa);
      return { bc, mar, base, fab, generico: !!pa, pa: pa ? paIni(pa, [N(base)]) : '', cesta: (cfg.categorias.find(c => c.nome === x.cat) || {}).cesta || 'OUTRA',
        cat: nomeOf(x.cat), marca: x.marca, fabR: x.fab, desc: x.desc }; }); }, exp);
  const n = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().replace(/[^A-Z0-9]+/g, ' ').trim();
  let okM = 0, okF = 0, farma = 0; const erros = [];
  for (const x of r) {
    const marcaEsp = x.generico ? x.pa : x.base;
    const mOk = n(x.marca) === n(marcaEsp), fOk = n(x.fabR) === n(x.fab) || /OUTRO FABRICANTE|SIN PROVEEDOR/.test(x.fab);
    okM += mOk; okF += fOk; farma += x.cesta === 'FARMACIA';
    if (!mOk || !fOk || x.cesta !== 'FARMACIA') erros.push(`${x.generico ? 'GEN' : 'COM'} ${x.mar.padEnd(28)} | marca ${String(x.marca).padEnd(22)} (esp. ${marcaEsp}) | fab ${String(x.fabR).padEnd(22)} (esp. ${x.fab}) | ${x.cat} | ${x.desc}`);
  }
  console.log(`${r.length} marcas: marca certa ${okM}, fabricante certo ${okF}, em Farmácia ${farma}; genéricos ${r.filter(x => x.generico).length}`);
  fs.writeFileSync(path.join(__dirname, 'hoja_erros.txt'), erros.join('\n') + '\n');
  await b.close();
})();
