// Amostra de 2.000 marcas de Farmácia da DIMA (todos os capítulos ATC) como descrições: quantas caem em OUTRA
// CATEGORIA, quantas ficam no código EST MER 6 certo (prefixo do nome oficial) e quantas saem da Farmácia.
// Uso: NODE_PATH=$(npm root -g) node testes_farma/rodar_dima.js [pagina.html]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const pagina = process.argv[2] || path.join(__dirname, '..', 'farmacia.html');
const exp = new Map(fs.readFileSync(path.join(__dirname, 'dima_amostra_esperado.tsv'), 'utf8').trim().split('\n').map(l => { const x = l.split('\t'); return [x[0], x]; }));
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  p.on('pageerror', e => console.error('ERRO', e.message));
  await p.setContent(require('fs').readFileSync(pagina, 'utf8'), { waitUntil: 'load', timeout: 120000 }); // a página não declara charset (o artifact recebe do serviço)
  await p.waitForFunction(() => typeof data !== 'undefined' && data.dima, null, { timeout: 60000 });
  await p.evaluate(() => { for (const c of cfg.categorias) c.ativa = true; renderCats(); });
  await p.setInputFiles('#fBacklog', path.join(__dirname, 'dima_amostra.csv'));
  await p.waitForFunction(() => !document.querySelector('#btnRun').disabled, null, { timeout: 60000 });
  await p.click('#btnRun');
  await p.waitForFunction(() => data.results && data.results.length, null, { timeout: 300000 });
  const r = await p.evaluate(() => data.results.map(x => ({ bc: String(x.it.barcode), cat: nomeOf(x.cat), cesta: (cfg.categorias.find(c => c.nome === x.cat) || {}).cesta || '', marca: x.marca, fab: x.fab, desc: x.desc, d: x.it.D[0] })));
  let out = 0, farma = 0, cod = 0, fab = 0; const linhas = [];
  for (const x of r) {
    const [, m, seg, f] = exp.get(x.bc); const c6 = seg.split(' ')[0];
    if (x.cat === 'OUTRA CATEGORIA') out++;
    if (x.cesta === 'FARMACIA') farma++;
    const ok = x.cat.startsWith(c6); if (ok) cod++;
    if (x.fab === f || /OUTRO FABRICANTE/.test(f)) fab++;
    if (!ok) linhas.push(`${m.padEnd(30)} | esp. ${seg.slice(0, 40).padEnd(40)} | app ${x.cat}`);
  }
  console.log(`${r.length} itens: OUTRA CATEGORIA ${out}, em Farmácia ${farma}, EST MER 6 certa ${cod}, fabricante certo ${fab}`);
  fs.writeFileSync(path.join(__dirname, 'dima_erros.txt'), linhas.join('\n') + '\n');
  await b.close();
})();
