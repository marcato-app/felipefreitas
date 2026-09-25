// Roda os casos de teste de Farmácia no classificador.html (Playwright).
// Uso: NODE_PATH=$(npm root -g) node testes_farma/rodar.js [arquivo.csv ...]
const { chromium } = require('playwright');
const path = require('path');
const dir = path.join(__dirname, '..');
const casos = process.argv.slice(2).length ? process.argv.slice(2)
  : ['farma_categoria.csv', 'farma_laboratorio.csv', 'farma_nome_oficial.csv'].map(f => path.join(dir, 'farma_pacote/testes', f));
(async () => {
  const b = await chromium.launch();
  for (const f of casos) {
    const p = await b.newPage();
    p.on('pageerror', e => console.error('ERRO', e.message));
    await p.goto('file://' + path.join(dir, 'classificador.html'));
    await p.waitForFunction(() => typeof data !== 'undefined' && data.dima, null, { timeout: 60000 });
    await p.evaluate(() => { for (const c of cfg.categorias) c.ativa = true; renderCats(); }); // todas as categorias ativas
    await p.setInputFiles('#fBacklog', f);
    await p.waitForFunction(() => !document.querySelector('#btnRun').disabled, null, { timeout: 60000 });
    await p.click('#btnRun');
    await p.waitForFunction(() => data.results && data.results.length, null, { timeout: 120000 });
    const r = await p.evaluate(() => data.results.map(x => ({ d: x.it.descs ? x.it.descs[0] : (x.it.desc || ''), cat: nomeOf(x.cat), marca: x.marca, fab: x.fab, desc: x.desc, alerts: x.alerts, pri: x.pri })));
    console.log('== ' + path.basename(f));
    for (const x of r) console.log(`${String(x.d).padEnd(48)} => ${x.cat}\n${' '.repeat(51)}${x.desc} | ${x.marca} | ${x.fab}\n${' '.repeat(51)}${JSON.stringify(x.alerts)} pri=${x.pri}`);
    await p.close();
  }
  await b.close();
})();
