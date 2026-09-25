// Arquivo de descrições das lojas (SKU x loja x descrição) -> classifica e mostra a descrição escolhida.
// Uso: NODE_PATH=$(npm root -g) node testes_farma/rodar_lojas.js <lojas.csv> [backlog.csv]
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const [lojas, backlog] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); p.on('pageerror', e => console.error('ERRO', e.message));
  await p.setContent(fs.readFileSync(path.join(__dirname, '..', 'farmacia.html'), 'utf8'), { waitUntil: 'load', timeout: 120000 });
  await p.waitForFunction(() => typeof data !== 'undefined' && data.dima, null, { timeout: 60000 });
  if (backlog) { await p.setInputFiles('#fBacklog', backlog); await p.waitForFunction(() => data.items, null, { timeout: 60000 }); }
  if (lojas) { await p.setInputFiles('#fLojas', lojas); await p.waitForFunction(() => data.lojas && !document.querySelector('#btnRun').disabled, null, { timeout: 60000 }); }
  await p.waitForFunction(() => !document.querySelector('#btnRun').disabled, null, { timeout: 60000 });
  await p.click('#btnRun');
  await p.waitForFunction(() => data.results && data.results.length, null, { timeout: 300000 });
  const r = await p.evaluate(() => data.results.map(x => ({ bc: String(x.it.barcode), loja: x.it.lojaUsada || x.it.D[0], cat: nomeOf(x.cat), marca: x.marca, fab: x.fab, qt: x.qt, base: x.qbase, desc: x.desc })));
  let un1 = 0, out = 0;
  for (const x of r) { if (x.qt === 1 && x.base === 'UN') un1++; if (x.cat === 'OUTRA CATEGORIA') out++;
    console.log(`${x.loja.slice(0, 44).padEnd(44)} | ${x.cat.slice(0, 34).padEnd(34)} | ${String(x.marca).slice(0, 14).padEnd(14)} | ${String(x.fab).slice(0, 16).padEnd(16)} | ${x.qt}${x.base} | ${x.desc}`); }
  console.log(`${r.length} SKUs: 1UN ${un1}, OUTRA CATEGORIA ${out}`);
  await b.close();
})();
