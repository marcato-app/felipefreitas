// Categoria VITAMINA E MINERAL inteira (base do cliente, dados/vitaminas/vitamina_mineral.tsv): entra só a descrição
// das lojas (TOP/MAX); compara EST MER 7, marca, fabricante e conteúdo com o que o cliente tem e grava o descritivo novo.
// Uso: NODE_PATH=$(npm root -g) node testes_farma/rodar_vit.js [pagina.html]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const pagina = process.argv[2] || path.join(__dirname, '..', 'farmacia.html');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  p.on('pageerror', e => console.error('ERRO', e.message));
  await p.setContent(fs.readFileSync(pagina, 'utf8'), { waitUntil: 'load', timeout: 120000 });
  await p.waitForFunction(() => typeof data !== 'undefined' && data.dima, null, { timeout: 60000 });
  await p.setInputFiles('#fBacklog', path.join(__dirname, 'vitaminas.csv'));
  await p.waitForFunction(() => !document.querySelector('#btnRun').disabled, null, { timeout: 60000 });
  await p.evaluate(() => { if (typeof irEtapa === 'function') irEtapa(6); }); await p.click('#btnRun');
  await p.waitForFunction(() => data.results && data.results.length, null, { timeout: 600000 });
  const r = await p.evaluate(() => data.results.map(x => [String(x.it.barcode), x.it.D[0] || '', nomeOf(x.cat), x.marca, x.fab, x.desc, x.qt, !!x.it.vitReg, x.it.vit ? (x.it.vit.nut ?? -1) : null]));
  fs.writeFileSync(process.env.SAIDA || path.join(__dirname, 'vitaminas_saida.json'), JSON.stringify(r));
  console.log(r.length + ' itens');
  await b.close();
})();
