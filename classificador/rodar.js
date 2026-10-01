// Roda o classificador.html fora do navegador do usuário (Chromium headless, mais memória) e salva a planilha.
// Uso: NODE_PATH=$(npm root -g) node rodar.js <backlog.xlsx|csv> [--so-descritivo|--priorizar|--sempre] [--dict dicionario.xlsx] [--saida pasta]
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const args = process.argv.slice(2); const file = path.resolve(args.find(a => !a.startsWith('--') && !args[args.indexOf(a) - 1]?.startsWith('--d') && !args[args.indexOf(a) - 1]?.startsWith('--s')) || '');
const opt = n => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
const modo = args.includes('--sempre') ? 'sempre' : args.includes('--priorizar') ? 'priorizar' : 'so';
const dict = opt('--dict'); const saida = path.resolve(opt('--saida') || path.join(__dirname, 'saida'));
const XLSXJS = process.env.XLSXJS; // opcional: cópia local do xlsx.full.min.js (sem internet)
(async () => {
  fs.mkdirSync(saida, { recursive: true });
  const b = await chromium.launch({ args: ['--js-flags=--max-old-space-size=8192'] }); const ctx = await b.newContext({ acceptDownloads: true });
  if (XLSXJS) await ctx.route(/cdnjs.*xlsx/, r => r.fulfill({ path: XLSXJS, contentType: 'text/javascript' }));
  const p = await ctx.newPage(); p.on('pageerror', e => console.log('ERRO', e.message));
  await p.goto('file://' + path.join(__dirname, 'classificador.html')); await p.waitForFunction(() => typeof cfg !== 'undefined', null, { timeout: 120000 });
  await p.evaluate(m => { for (const c of cfg.categorias) c.ativa = true; cfg.soDescritivo = m === 'so'; cfg.sempreArquivo = m === 'sempre'; cfg.priorizarArquivo = true; }, modo);
  if (dict) { await p.setInputFiles('#fDict', path.resolve(dict)); await p.waitForTimeout(3000); }
  let t = Date.now(); await p.setInputFiles('#fBacklog', file);
  await p.waitForFunction(() => data.items && data.items.length, null, { timeout: 900000 });
  console.log('lidos', await p.evaluate(() => data.items.length), 'itens em', (Date.now() - t) / 1000, 's |', (await p.evaluate(() => data.colunas || '')).replace(/<[^>]+>/g, ''));
  t = Date.now(); await p.evaluate(() => setTimeout(() => document.querySelector('#btnRun').click(), 0));
  const tick = setInterval(async () => { try { console.log('  ', await p.textContent('#runState')); } catch (_) {} }, 30000);
  await p.waitForFunction(() => data.results && data.results.length, null, { timeout: 7200000, polling: 2000 }); clearInterval(tick);
  console.log(await p.textContent('#runState')); console.log((await p.textContent('#marcaMot')) || '');
  t = Date.now(); const [d] = await Promise.all([p.waitForEvent('download', { timeout: 3600000 }), p.evaluate(() => setTimeout(() => document.querySelector('#btnDownload').click(), 0))]);
  const out = path.join(saida, path.basename(file).replace(/\.[^.]+$/, '') + '_CLASSIFICADO.xlsx'); await d.saveAs(out);
  console.log('salvo', out, (fs.statSync(out).size / 1e6).toFixed(1), 'MB em', (Date.now() - t) / 1000, 's'); await b.close();
})().catch(e => { console.error(e); process.exit(1); });
