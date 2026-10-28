// Confere a função "Padronizar descritivo + sugestões" com testes/sugestao_exemplo.xlsx:
// as colunas do arquivo saem idênticas e o descritivo / as sugestões batem com o esperado.
// Uso: NODE_PATH=... node testes/testar_sugestao.js classificador.html xlsx.full.min.js
const { chromium } = require('playwright'); const path = require('path');
const [,, html, xlsxjs] = process.argv; const file = path.join(__dirname, 'sugestao_exemplo.xlsx');
// [linha, descritivo, marca sugerida, fabricante sugerido, quantidade sugerida, categoria sugerida]
const ESP = [
  [1, 'CORTADOR DE UNHA UTIL MIL 1UN', 'UTIL MIL', 'UTIL MIL', '', ''],
  [2, 'CORTADOR DE UNHA CHAZAK ACO 1UN', 'CHAZAK', 'CHAZAK IMPORTACOES', '', ''],
  [3, 'ALICATES DE CUTICULA ALTO GIRO 1UN', 'ALTO GIRO', 'ALTO GIRO ENCARTELADORA LTDA', '', ''],
  [4, 'CORTADOR DE UNHA BELLIZ GRANDE 1UN', 'RICCA', '', '', ''],
  [5, null, 'ETIHOME', 'ETILUX', '', ''],
  [6, null, '', 'LUXCAR', '', ''],
  [7, 'CORTADOR DE UNHA RIO TIJUCAS 1UN', 'RIO TIJUCAS', 'RIO TIJUCAS', '', ''],
  [8, 'TESOURA DE UNHA EASE CARE 1UN', '', '', '', ''],
  [9, null, '', '', '', ''],
  [10, 'LIXA DE UNHA CAPRICHOSA OURO 1UN', '', '', 6, ''],
  [11, 'LEITE CONDENSADO MOCA 395G', '', '', '', ''],
  [14, 'LEITE CONDENSADO MOCA 12X395G', '', '', '', ''],
  [15, null, '', '', '', 'REFRIGERANTE'],
  [16, 'ARROZ BRANCO TIO JOAO 5KG', 'TIO JOAO', 'JOSAPAR SA', 5000, 'ARROZ BRANCO'],
  [17, 'GARRAFA TERMICA ALADDIN AZEITONA 1L 6X1UN', '', '', '', ''], // sem TERMICO / ALADIN repetidos
  [18, 'BISCOITO RECHEADO NESTLE CHOCOLATE 140G', '', 'DPA', '', ''], // sem RECHEADA / NESTLLE
];
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext();
  await ctx.route(/cdnjs.*xlsx/, r => r.fulfill({ path: xlsxjs, contentType: 'text/javascript' }));
  const p = await ctx.newPage(); await p.goto('file://' + path.resolve(html)); await p.waitForFunction(() => typeof cfg !== 'undefined', null, { timeout: 240000 });
  await p.evaluate(() => { for (const c of cfg.categorias) c.ativa = true; });
  await p.setInputFiles('#fBacklog', file); await p.waitForFunction(() => data.items && data.items.length && !document.querySelector('#btnSug').disabled, null, { timeout: 240000 });
  await p.click('#btnSug'); await p.waitForFunction(() => data.results && data.results.modoSug, null, { timeout: 900000 });
  const out = await p.evaluate(() => { const wb = XLSX.read(buildWorkbook(), { type: 'array' }); return XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { header: 1, raw: true, defval: '' }); });
  const inp = await p.evaluate(async () => [data.hdr, ...data.items.map(i => i.row)]);
  let ok = 0, n = 0; const W = inp[0].length;
  for (let i = 0; i < inp.length; i++) { n++; const a = JSON.stringify((inp[i] || []).slice(0, W).map(v => v ?? '')), o = JSON.stringify(out[i].slice(0, W)); if (a === o) ok++; else console.log('COLUNA DO ARQUIVO MUDOU na linha', i + 1, a, o); }
  for (const [i, d, m, f, q, c] of ESP) { n++; const r = out[i].slice(W); const exp = [d ?? r[0], m, f, q, c];
    if (JSON.stringify(r) === JSON.stringify(exp)) ok++; else console.log('ERRO linha', i + 1, '| esperado', JSON.stringify(exp), '| saiu', JSON.stringify(r)); }
  // regra da marca: com marca no arquivo, o descritivo leva a marca do arquivo; com OUTRA MARCA, a marca sugerida (se houver)
  const iM = inp[0].findIndex(h => String(h).trim().toUpperCase() === 'MARCA'); const norm = v => String(v ?? '').toUpperCase().replace(/\s+/g, ' ').trim();
  for (let i = 1; i < out.length; i++) { n++; const m = norm(out[i][iM]), d = ' ' + norm(out[i][W]) + ' ', sg = norm(out[i][W + 1]);
    const exp = m && m !== 'OUTRA MARCA' ? m : sg; if (!exp || d.includes(' ' + exp + ' ')) ok++; else console.log('MARCA ERRADA NO DESCRITIVO linha', i + 1, '| esperado', exp, '| descritivo', d.trim()); }
  console.log(`${ok} de ${n} verificações corretas`); await b.close(); process.exit(ok === n ? 0 : 1);
})();
