// Confere os exemplos ensinados pelo usuário (testes/regras_ensinadas.csv) contra o classificador.html.
// marca_esperada = * : só confere a categoria.
// Uso: NODE_PATH=/opt/node22/lib/node_modules node testes/testar_regras.js classificador.html caminho/xlsx.full.min.js
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const [,, html, xlsxjs] = process.argv; const csv = path.join(__dirname, 'regras_ensinadas.csv');
const esperado = fs.readFileSync(csv, 'utf8').trim().split('\n').slice(1).map(l => l.split(';')).map(c => ({ cat: c[c.length - 2], marca: c[c.length - 1] }));
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext();
  await ctx.route(/cdnjs.*xlsx/, r => r.fulfill({ path: xlsxjs, contentType: 'text/javascript' }));
  const p = await ctx.newPage(); await p.goto('file://' + path.resolve(html)); await p.waitForFunction(() => typeof cfg !== 'undefined', null, { timeout: 180000 });
  await p.evaluate(() => { for (const c of cfg.categorias) c.ativa = true; });
  await p.setInputFiles('#fBacklog', csv); await p.waitForFunction(() => data.items && data.items.length, null, { timeout: 180000 });
  await p.click('#btnRun'); await p.waitForFunction(() => data.results && data.results.length, null, { timeout: 600000 });
  const r = await p.evaluate(() => data.results.map(x => ({ d: x.it.D[0], cat: x.cat, marca: x.marca, desc: x.desc })));
  let erros = 0; r.forEach((x, i) => { const e = esperado[i]; if (x.cat !== e.cat || (e.marca !== '*' && x.marca !== e.marca)) { erros++; console.log('ERRO', x.d, '| esperado', e.cat, '/', e.marca, '| saiu', x.cat, '/', x.marca, '|', x.desc); } });
  console.log(`${r.length - erros} de ${r.length} exemplos ensinados corretos`); await b.close(); process.exit(erros ? 1 : 0);
})();
