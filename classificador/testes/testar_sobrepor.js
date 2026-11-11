// Confere o modo "Sugestões sobrepostas no arquivo" do Padronizar descritivo + sugestões com testes/sugestao_exemplo.xlsx:
// a sugestão entra na própria coluna, a célula fica destacada (preenchimento sólido) e o valor anterior vai para AJUSTES DO APP.
// Uso: NODE_PATH=... node testes/testar_sobrepor.js classificador.html xlsx.full.min.js
const { chromium } = require('playwright'); const path = require('path');
const [,, html, xlsxjs] = process.argv; const file = path.join(__dirname, 'sugestao_exemplo.xlsx');
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext();
  await ctx.route(/cdnjs.*xlsx/, r => r.fulfill({ path: xlsxjs, contentType: 'text/javascript' }));
  const p = await ctx.newPage(); await p.goto('file://' + path.resolve(html)); await p.waitForFunction(() => typeof cfg !== 'undefined', null, { timeout: 240000 });
  await p.evaluate(() => { for (const c of cfg.categorias) c.ativa = true; });
  await p.setInputFiles('#fBacklog', file); await p.waitForFunction(() => data.items && data.items.length && !document.querySelector('#btnSug').disabled, null, { timeout: 240000 });
  await p.click('#btnSug'); await p.waitForFunction(() => data.results && data.results.modoSug, null, { timeout: 900000 });
  const r = await p.evaluate(() => {
    cfg.sugModo = 'colunas'; const sep = XLSX.read(buildWorkbook(), { type: 'array' }); const A = XLSX.utils.sheet_to_json(sep.Sheets[sep.SheetNames[0]], { header: 1, defval: '' });
    cfg.sugModo = 'sobrepor'; const buf = buildWorkbook(); const sob = XLSX.read(buf, { type: 'array' }); const B = XLSX.utils.sheet_to_json(sob.Sheets[sob.SheetNames[0]], { header: 1, defval: '' });
    const z = XLSX.CFB.read(new Uint8Array(buf), { type: 'array' }); const sh = new TextDecoder().decode(z.FileIndex[z.FullPaths.findIndex(x => x.endsWith('/xl/worksheets/sheet1.xml'))].content);
    const st = new TextDecoder().decode(z.FileIndex[z.FullPaths.findIndex(x => x.endsWith('/xl/styles.xml'))].content);
    cfg.sugModo = 'colunas'; return { A, B, sh, st, hdr: data.hdr };
  });
  let ok = 0, n = 0; const t = (c, msg) => { n++; if (c) ok++; else console.log('ERRO:', msg); };
  const hA = r.A[0], hB = r.B[0]; const iM = hB.indexOf('MARCA'), iMs = hA.indexOf('MARCA SUGERIDA'), iAj = hB.indexOf('AJUSTES DO APP');
  t(iAj >= 0, 'coluna AJUSTES DO APP'); t(r.st.includes('patternType="solid"'), 'preenchimento no styles.xml');
  const sId = (/<xf numFmtId="0" fontId="0" fillId="\d+" borderId="0" xfId="0" applyFill="1"\/>/.test(r.st));
  t(sId, 'xf com preenchimento');
  for (let i = 1; i < r.A.length; i++) {
    const sug = r.A[i][iMs];
    if (sug) { t(String(r.B[i][iM]) === String(sug), `linha ${i + 1}: marca sobreposta (${r.B[i][iM]} x ${sug})`); t(String(r.B[i][iAj]).includes('MARCA:'), `linha ${i + 1}: ajuste registrado`);
      const ref = String.fromCharCode(65 + iM) + (i + 1); t(new RegExp(`<c r="${ref}"[^>]* s="\\d+"`).test(r.sh), `linha ${i + 1}: célula ${ref} destacada`); }
    else t(String(r.B[i][iM]) === String(r.A[i][iM]), `linha ${i + 1}: marca sem sugestão fica igual`);
  }
  console.log(`${ok} de ${n} verificações corretas`); await b.close(); process.exit(ok === n ? 0 : 1);
})();
