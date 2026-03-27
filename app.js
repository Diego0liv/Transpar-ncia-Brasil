const API = 'const API_URL = "https://transpar-ncia-brasil-production.up.railway.app";';
let todosEstados = [];
let filtroAtivo  = 'todos';
let chartComparar = null;
let chartRadar    = null;
let govData       = [];

function scoreColor(s) {
  if (s >= 75) return '#16a34a';
  if (s >= 55) return '#65a30d';
  if (s >= 35) return '#ca8a04';
  return '#dc2626';
}

function rankClass(i) {
  return i === 1 ? 'gold' : i === 2 ? 'silver' : i === 3 ? 'bronze' : 'other';
}

// ── PAINEL NACIONAL ──
async function carregarResumo() {
  try {
    const r = await fetch(`${API}/resumo`, { signal: AbortSignal.timeout(3000) });
    if (!r.ok) return;
    const d = await r.json();
    const m = d.medias_nacionais;
    document.getElementById('pEdu').textContent = m.educacao;
    document.getElementById('pSau').textContent = m.saude;
    document.getElementById('pSeg').textContent = m.seguranca;
    document.getElementById('pEco').textContent = m.economia;
    document.getElementById('pEduTrend').textContent = '↑ Score baseado em IDEB 2021';
    document.getElementById('pSauTrend').textContent = '↑ Score baseado em mortalidade infantil';
    document.getElementById('pSegTrend').textContent = '↓ Score baseado em homicídios/100k';
    document.getElementById('pEcoTrend').textContent = '↑ Score baseado em rendimento médio';
  } catch {}
}

// ── RANKING ──
function renderRanking(lista) {
  const tbody = document.getElementById('rankingBody');
  const sorted = [...lista].sort((a, b) => b.score - a.score);
  const filtrada = filtroAtivo === 'todos' ? sorted : sorted.filter(e => e.regiao === filtroAtivo);
  if (!filtrada.length) {
    tbody.innerHTML = '<tr><td colspan="8" style="padding:30px;text-align:center">Nenhum estado encontrado.</td></tr>';
    return;
  }
  tbody.innerHTML = filtrada.map((e, i) => {
    const pos = i + 1;
    const cor = scoreColor(e.score);
    return `<tr onclick="abrirModal('${e.uf}')">
      <td><div class="rank-pos ${rankClass(pos)}">${pos}</div></td>
      <td><span class="estado-name">${e.nome}</span><span class="uf-badge">${e.uf}</span></td>
      <td><span class="reg-badge reg-${e.regiao}">${e.regiao}</span></td>
      <td>${mini(e.educacao, '#3b82f6')}</td>
      <td>${mini(e.saude, '#009c3b')}</td>
      <td>${mini(e.seguranca, '#f59e0b')}</td>
      <td>${mini(e.economia, '#8b5cf6')}</td>
      <td><div class="bar-wrap">
        <div class="bar"><div class="bar-fill" style="width:${e.score}%;background:${cor}"></div></div>
        <span class="bar-num" style="color:${cor}">${e.score}</span>
      </div></td>
    </tr>`;
  }).join('');
}

function mini(val, cor) {
  return `<div class="bar-wrap">
    <div class="bar"><div class="bar-fill" style="width:${val}%;background:${cor}"></div></div>
    <span class="bar-num" style="color:${cor}">${val}</span>
  </div>`;
}

function filtrar(reg, btn) {
  filtroAtivo = reg;
  document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderRanking(todosEstados);
}

// ── MODAL DETALHE ESTADO ──
async function abrirModal(uf) {
  const overlay = document.getElementById('modalOverlay');
  overlay.classList.add('open');
  document.getElementById('modalNome').textContent = '...';
  try {
    const r = await fetch(`${API}/estados/${uf}`);
    const d = await r.json();
    document.getElementById('modalNome').textContent = d.nome;
    document.getElementById('modalSub').textContent = `${d.regiao} · Capital: ${d.capital || '—'}`;

    const s = d.score;
    const cor = scoreColor(s.geral);
    document.getElementById('modalScoreGeral').textContent = s.geral;
    document.getElementById('modalScoreGeral').style.color = cor;

    document.getElementById('scoresGrid').innerHTML = [
      { label: '📚 Educação', val: s.educacao, cor: '#3b82f6' },
      { label: '🏥 Saúde',    val: s.saude,    cor: '#009c3b' },
      { label: '🔒 Segurança',val: s.seguranca, cor: '#f59e0b' },
      { label: '💰 Economia', val: s.economia,  cor: '#8b5cf6' },
    ].map(it => `<div class="score-item">
      <div class="s-label">${it.label}</div>
      <div class="s-val" style="color:${it.cor}">${it.val}</div>
      <div class="s-bar"><div class="s-bar-fill" style="width:${it.val}%;background:${it.cor}"></div></div>
    </div>`).join('');

    if (chartRadar) chartRadar.destroy();
    chartRadar = new Chart(document.getElementById('chartRadar'), {
      type: 'radar',
      data: {
        labels: ['Educação','Saúde','Segurança','Economia'],
        datasets: [{
          label: d.uf,
          data: [s.educacao, s.saude, s.seguranca, s.economia],
          backgroundColor: 'rgba(0,39,118,.15)',
          borderColor: '#002776',
          pointBackgroundColor: '#002776',
          borderWidth: 2,
        }]
      },
      options: { scales: { r: { min: 0, max: 100, ticks: { stepSize: 25 } } }, plugins: { legend: { display: false } } }
    });

    const cats = d.indicadores || {};
    const rows = Object.values(cats).flat();
    document.getElementById('indList').innerHTML = rows.length ? rows.map(i => `
      <div class="ind-row">
        <span class="ind-name">${i.nome.replace(/_/g,' ')}</span>
        <span>
          <span class="ind-val">${i.valor ?? '—'} ${i.unidade ?? ''}</span>
          <span class="ind-fonte"> · ${i.fonte ?? ''} ${i.ano}</span>
        </span>
      </div>`).join('') : '<div style="color:var(--gray-text);font-size:.88rem">Sem indicadores detalhados.</div>';

  } catch { document.getElementById('modalNome').textContent = 'Erro ao carregar.'; }
}

function fecharModal(e) {
  if (!e || e.target === document.getElementById('modalOverlay') || e.currentTarget.classList.contains('modal-close')) {
    document.getElementById('modalOverlay').classList.remove('open');
    if (chartRadar) { chartRadar.destroy(); chartRadar = null; }
  }
}

// ── COMPARAR ──
async function compararEstados() {
  const input = document.getElementById('inputComparar').value;
  if (!input.trim()) return;
  const ufs = input.split(',').map(s => s.trim()).filter(Boolean).slice(0, 5).join(',');
  try {
    const r = await fetch(`${API}/comparar?ufs=${ufs}`);
    const data = await r.json();
    if (!data.length) return;

    document.getElementById('compCards').innerHTML = data.map(e => {
      const s = e.scores;
      const cor = scoreColor(s.geral);
      return `<div class="comp-card">
        <div class="comp-nome">${e.nome} <span class="uf-badge">${e.uf}</span></div>
        <div class="comp-score" style="color:${cor}">${s.geral}</div>
        <div class="comp-row"><span class="c-label">📚 Educação</span><span class="c-val">${s.educacao}</span></div>
        <div class="comp-row"><span class="c-label">🏥 Saúde</span><span class="c-val">${s.saude}</span></div>
        <div class="comp-row"><span class="c-label">🔒 Segurança</span><span class="c-val">${s.seguranca}</span></div>
        <div class="comp-row"><span class="c-label">💰 Economia</span><span class="c-val">${s.economia}</span></div>
      </div>`;
    }).join('');

    if (chartComparar) chartComparar.destroy();
    const cores = ['#002776','#009c3b','#f59e0b','#8b5cf6','#dc2626'];
    chartComparar = new Chart(document.getElementById('chartComparar'), {
      type: 'bar',
      data: {
        labels: ['Educação','Saúde','Segurança','Economia','Score Geral'],
        datasets: data.map((e, i) => ({
          label: e.uf,
          data: [e.scores.educacao, e.scores.saude, e.scores.seguranca, e.scores.economia, e.scores.geral],
          backgroundColor: cores[i % cores.length] + '99',
          borderColor: cores[i % cores.length],
          borderWidth: 2,
          borderRadius: 6,
        }))
      },
      options: {
        responsive: true,
        scales: { y: { min: 0, max: 100 } },
        plugins: { legend: { position: 'top' } }
      }
    });

    document.getElementById('compResultado').classList.add('show');
  } catch { alert('Erro ao comparar. Verifique as siglas.'); }
}

// ── SENADORES ──
async function carregarSenadores(pagina = 1) {
  const grid    = document.getElementById('senGrid');
  const uf      = document.getElementById('senFiltroUF')?.value || '';
  const partido = document.getElementById('senFiltroPartido')?.value || '';
  const busca   = document.getElementById('senBusca')?.value || '';
  grid.innerHTML = '<div style="grid-column:1/-1;padding:40px;text-align:center"><span class="spinner"></span> Carregando...</div>';

  let url = `${API}/politicos?cargo=senador&itens=27&pagina=${pagina}`;
  if (uf)      url += `&uf=${uf}`;
  if (partido) url += `&partido=${encodeURIComponent(partido)}`;
  if (busca)   url += `&busca=${encodeURIComponent(busca)}`;

  try {
    const r    = await fetch(url);
    const data = await r.json();
    renderPoliticos(data.dados, grid);
    renderPaginacaoElem(data.total, pagina, 27, 'carregarSenadores', 'senPaginacao');
  } catch {
    grid.innerHTML = '<div style="grid-column:1/-1;padding:30px;text-align:center;color:var(--gray-text)">Erro ao carregar senadores.</div>';
  }
}

// ── DEPUTADOS ──
let debounceTimer = null;
function debounce(tipo = 'deputado') {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => tipo === 'senador' ? carregarSenadores(1) : buscarPoliticos(1), 400);
}

async function carregarStatsPoliticos() {
  try {
    const [rDep, rSen, rPart] = await Promise.all([
      fetch(`${API}/politicos?cargo=deputado_federal&itens=1`),
      fetch(`${API}/politicos?cargo=senador&itens=1`),
      fetch(`${API}/partidos/resumo`),
    ]);
    const dep  = await rDep.json();
    const sen  = await rSen.json();
    const part = await rPart.json();
    document.getElementById('totalDep').textContent      = dep.total;
    document.getElementById('totalSen').textContent      = sen.total;
    document.getElementById('totalPartidos').textContent = part.length;
    document.getElementById('totalVotos').textContent    = '2.364';
  } catch {}
}

async function buscarPoliticos(pagina = 1) {
  const uf      = document.getElementById('filtroUF').value;
  const partido = document.getElementById('filtroPartido').value;
  const grid    = document.getElementById('polGrid');
  grid.innerHTML = '<div style="grid-column:1/-1;padding:40px;text-align:center"><span class="spinner"></span> Carregando...</div>';

  let url = `${API}/politicos?cargo=deputado_federal&itens=24&pagina=${pagina}`;
  if (uf)      url += `&uf=${uf}`;
  if (partido) url += `&partido=${encodeURIComponent(partido)}`;

  try {
    const r    = await fetch(url);
    const data = await r.json();
    renderPoliticos(data.dados, grid);
    renderPaginacaoElem(data.total, pagina, 24, 'buscarPoliticos', 'polPaginacao');
  } catch {
    grid.innerHTML = '<div style="grid-column:1/-1;padding:30px;text-align:center;color:var(--gray-text)">Erro ao carregar deputados.</div>';
  }
}

function renderPoliticos(lista, grid) {
  if (!lista.length) {
    grid.innerHTML = '<div style="grid-column:1/-1;padding:30px;text-align:center;color:var(--gray-text)">Nenhum resultado.</div>';
    return;
  }
  grid.innerHTML = lista.map(p => {
    const cargoClass = p.cargo === 'senador' ? 'cargo-sen' : 'cargo-dep';
    const cargoLabel = p.cargo === 'senador' ? 'Senador(a)' : 'Dep. Federal';
    const foto = p.foto_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(p.nome)}&background=002776&color=ffdf00&size=80`;
    const sg = p.score_geral;
    const corSg = sg >= 8 ? '#16a34a' : sg >= 5 ? '#ca8a04' : sg != null ? '#dc2626' : '#999';
    const scoreHtml = sg != null
      ? `<span class="pol-score-item">Score <strong style="color:${corSg}">${sg}/10</strong></span>`
      : '';
    const presenca  = p.score_presenca  != null ? `<span class="pol-score-item">Presença <strong>${p.score_presenca}%</strong></span>` : '';
    const atividade = p.score_atividade != null ? `<span class="pol-score-item">Votos <strong>${p.score_atividade}</strong></span>` : '';
    return `<div class="pol-card" onclick="abrirModalPol(${p.id})">
      <img class="pol-foto" src="${foto}" alt="${p.nome}" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(p.nome)}&background=eef1f7&color=002776&size=80'" />
      <div class="pol-info">
        <div class="pol-nome" title="${p.nome}">${p.nome}</div>
        <div class="pol-meta">${p.partido || '—'} · ${p.uf || '—'}</div>
        <span class="pol-cargo ${cargoClass}">${cargoLabel}</span>
        <div class="pol-score-row">${scoreHtml}${presenca}${atividade}</div>
      </div>
    </div>`;
  }).join('');
}

function renderPaginacaoElem(total, atual, itens, fnName, elemId) {
  const totalPag = Math.ceil(total / itens);
  const pag = document.getElementById(elemId);
  if (!pag) return;
  if (totalPag <= 1) { pag.innerHTML = ''; return; }
  const inicio = Math.max(1, atual - 2);
  const fim    = Math.min(totalPag, atual + 2);
  let html = '';
  if (atual > 1)        html += `<button class="btn-pag" onclick="${fnName}(${atual - 1})">‹</button>`;
  for (let i = inicio; i <= fim; i++) {
    html += `<button class="btn-pag ${i === atual ? 'ativo' : ''}" onclick="${fnName}(${i})">${i}</button>`;
  }
  if (atual < totalPag) html += `<button class="btn-pag" onclick="${fnName}(${atual + 1})">›</button>`;
  html += `<span style="font-size:.8rem;color:var(--gray-text);margin-left:8px">${total} resultados</span>`;
  pag.innerHTML = html;
}

// ── MODAL POLÍTICO INTELIGENTE ──
function tagClass(tag) {
  const verdes   = ['Alto desempenho','Presença exemplar','Alinhado ao partido'];
  const amarelos = ['Voto independente','Pró-governo'];
  const vermelhos= ['Alta ausência'];
  if (verdes.includes(tag))    return 'tag-green';
  if (amarelos.includes(tag))  return 'tag-yellow';
  if (vermelhos.includes(tag)) return 'tag-red';
  return 'tag-blue';
}

function barraHtml(val, cor, max = 100) {
  const pct = val != null ? Math.min(100, (val / max) * 100) : 0;
  return `<div class="bar-progress"><div class="bar-progress-fill" style="width:${pct}%;background:${cor}"></div></div>`;
}

function gerarAlertas(d) {
  const alertas = [];
  const s = d.scores;
  if (s.alinhamento_partido != null && s.alinhamento_partido < 60)
    alertas.push({ tipo: 'perigo', icone: '⚠️', txt: `Vota diferente do ${d.partido} em <strong>${100 - s.alinhamento_partido}%</strong> das votações` });
  if (s.alinhamento_governo != null && s.alinhamento_governo > 85)
    alertas.push({ tipo: 'info', icone: '🏛️', txt: `Altamente alinhado ao governo federal: <strong>${s.alinhamento_governo}%</strong>` });
  if (s.alinhamento_governo != null && s.alinhamento_governo < 30)
    alertas.push({ tipo: 'perigo', icone: '🚨', txt: `Forte oposição ao governo: vota com PT em apenas <strong>${s.alinhamento_governo}%</strong>` });
  if (s.presenca != null && s.presenca < 60)
    alertas.push({ tipo: 'perigo', icone: '🔴', txt: `Presença muito baixa: <strong>${s.presenca}%</strong> das votações` });
  if (s.presenca != null && s.presenca >= 95)
    alertas.push({ tipo: 'sucesso', icone: '✅', txt: `Presença exemplar: <strong>${s.presenca}%</strong> das votações` });
  return alertas;
}

function votoIcone(voto) {
  if (!voto) return { cls: 'voto-out', txt: '—' };
  const v = voto.toLowerCase();
  if (v === 'sim')        return { cls: 'voto-sim', txt: '✅ Sim' };
  if (v === 'não' || v === 'nao') return { cls: 'voto-nao', txt: '❌ Não' };
  if (v.includes('absten')) return { cls: 'voto-abs', txt: '🟡 Abstenção' };
  return { cls: 'voto-out', txt: voto };
}

async function abrirModalPol(id) {
  const overlay = document.getElementById('modalPolOverlay');
  overlay.classList.add('open');

  document.getElementById('modalPolNome').textContent = 'Carregando...';
  document.getElementById('modalPolSub').textContent  = '';
  document.getElementById('modalPolScores').innerHTML = '';
  document.getElementById('modalPolVotosResumo').innerHTML = '<span class="spinner"></span>';
  document.getElementById('modalPolVotacoes').innerHTML    = '';

  try {
    const r = await fetch(`${API}/politicos/${id}`);
    const d = await r.json();
    const s = d.scores;

    const foto = d.foto_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(d.nome)}&background=002776&color=ffdf00&size=80`;
    document.getElementById('modalPolFoto').src         = foto;
    document.getElementById('modalPolNome').textContent = d.nome;
    document.getElementById('modalPolSub').textContent  =
      `${d.cargo === 'senador' ? 'Senador(a)' : 'Dep. Federal'} · ${d.partido} · ${d.uf}`;

    const corScore = s.geral >= 8 ? '#16a34a' : s.geral >= 5 ? '#ca8a04' : '#dc2626';

    // Seção de scores
    document.getElementById('modalPolScores').innerHTML = `
      <div class="score-geral-badge">
        <div>
          <div class="score-big-num" style="color:${corScore}">${s.geral ?? '—'}</div>
          <div class="score-big-label">Score Geral / 10</div>
        </div>
        <div style="flex:1">
          <div style="font-size:.82rem;color:rgba(255,255,255,.7)">
            ${d.classificacao.produtividade.icone} Produtividade: <strong style="color:white">${d.classificacao.produtividade.label}</strong>
            &nbsp;·&nbsp;
            ${d.classificacao.presenca.icone} Presença: <strong style="color:white">${d.classificacao.presenca.label}</strong>
          </div>
          <div class="smart-tags" style="margin-top:10px">
            ${(d.tags||[]).map(t => `<span class="smart-tag ${tagClass(t)}">${t}</span>`).join('')}
          </div>
        </div>
      </div>`;

    // Alertas inteligentes
    const alertas = gerarAlertas(d);
    const alertasHtml = alertas.map(a =>
      `<div class="alerta-box ${a.tipo}"><span class="alerta-icon">${a.icone}</span><span class="alerta-txt">${a.txt}</span></div>`
    ).join('');

    // Métricas detalhadas
    const metricas = `
      <div class="smart-section">
        <h4>📊 Desempenho</h4>
        <div class="metric-row">
          <span class="metric-label">Presença nas votações</span>
          ${barraHtml(s.presenca, '#009c3b')}
          <span class="metric-val">${s.presenca != null ? s.presenca + '%' : '—'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Total de votos registrados</span>
          <span class="metric-val">${s.atividade ?? '—'}</span>
        </div>
      </div>
      <div class="smart-section">
        <h4>🗳️ Comportamento de Voto</h4>
        <div class="metric-row">
          <span class="metric-label">Alinhamento com o partido (${d.partido})</span>
          ${barraHtml(s.alinhamento_partido, '#3b82f6')}
          <span class="metric-val">${s.alinhamento_partido != null ? s.alinhamento_partido + '%' : '—'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Alinhamento com o governo (PT)</span>
          ${barraHtml(s.alinhamento_governo, '#8b5cf6')}
          <span class="metric-val">${s.alinhamento_governo != null ? s.alinhamento_governo + '%' : '—'}</span>
        </div>
      </div>
      ${alertasHtml ? `<div class="smart-section"><h4>🚨 Alertas Inteligentes</h4>${alertasHtml}</div>` : ''}`;

    document.getElementById('modalPolVotosResumo').innerHTML = metricas;

    // Resumo votos + lista
    const rv = d.resumo_votos || {};
    const totalVotos = Object.values(rv).reduce((a, b) => a + b, 0);
    const resumoHtml = Object.entries(rv).sort((a, b) => b[1] - a[1]).map(([tipo, qtd]) => {
      const ic = votoIcone(tipo);
      const pct = totalVotos ? Math.round(qtd / totalVotos * 100) : 0;
      return `<div class="metric-row">
        <span class="${ic.cls}" style="font-size:.82rem">${ic.txt}</span>
        ${barraHtml(pct, ic.cls === 'voto-sim' ? '#16a34a' : ic.cls === 'voto-nao' ? '#dc2626' : '#ca8a04')}
        <span class="metric-val">${qtd} <span style="color:var(--gray-text);font-weight:400">(${pct}%)</span></span>
      </div>`;
    }).join('');

    const uvs = d.ultimas_votacoes || [];
    const votacoesHtml = uvs.length
      ? uvs.map(v => {
          const ic = votoIcone(v.voto);
          const dataStr = v.data && v.data !== 'None' ? `<span style="font-size:.7rem;color:#999;margin-left:4px">${v.data.slice(0,10)}</span>` : '';
          return `<div class="voto-icon-row">
            <span class="voto-prop-txt">${v.proposicao || '—'}${dataStr}</span>
            <span class="${ic.cls}">${ic.txt}</span>
          </div>`;
        }).join('')
      : '<div style="color:var(--gray-text);font-size:.86rem;padding:8px 0">Nenhuma votação registrada.</div>';

    document.getElementById('modalPolVotacoes').innerHTML = `
      <div class="smart-section">
        <h4>🗳️ Distribuição dos Votos</h4>
        ${resumoHtml || '<span style="color:var(--gray-text);font-size:.86rem">Sem dados</span>'}
      </div>
      <div class="smart-section">
        <h4>🔥 Votações Recentes</h4>
        <div style="max-height:260px;overflow-y:auto">${votacoesHtml}</div>
      </div>`;

  } catch(e) {
    document.getElementById('modalPolNome').textContent = 'Erro ao carregar.';
    console.error(e);
  }
}

function fecharModalPol(e) {
  if (!e || e.target === document.getElementById('modalPolOverlay') || e.currentTarget?.classList.contains('modal-close')) {
    document.getElementById('modalPolOverlay').classList.remove('open');
  }
}

// ── COMPARADOR DE POLÍTICOS ──
async function compararPoliticos() {
  const nomes = [
    document.getElementById('compPolInput1').value.trim(),
    document.getElementById('compPolInput2').value.trim(),
    document.getElementById('compPolInput3').value.trim(),
  ].filter(Boolean);

  if (nomes.length < 2) {
    alert('Digite ao menos 2 nomes para comparar.');
    return;
  }

  const res = document.getElementById('compPolResultado');
  res.innerHTML = '<div style="padding:30px;text-align:center"><span class="spinner"></span> Buscando...</div>';

  try {
    // Buscar IDs pelos nomes
    const ids = [];
    for (const nome of nomes) {
      const r = await fetch(`${API}/politicos?busca=${encodeURIComponent(nome)}&itens=1`);
      const d = await r.json();
      if (d.dados.length) ids.push(d.dados[0].id);
    }
    if (ids.length < 2) { res.innerHTML = '<div style="padding:20px;color:var(--gray-text)">Não foi possível encontrar os políticos informados.</div>'; return; }

    const r2 = await fetch(`${API}/comparar/politicos?ids=${ids.join(',')}`);
    const lista = await r2.json();

    const CORES = ['#002776','#009c3b','#f59e0b','#dc2626'];
    const maxAtiv = Math.max(...lista.map(p => p.score_atividade || 0)) || 1;

    res.innerHTML = `
      <div class="comp-pol-grid">
        ${lista.map((p, i) => {
          const cor = CORES[i % CORES.length];
          const corScore = p.score_geral >= 8 ? '#16a34a' : p.score_geral >= 5 ? '#ca8a04' : '#dc2626';
          const foto = p.foto_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(p.nome)}&background=${cor.replace('#','')}&color=ffffff&size=80`;
          return `<div class="comp-pol-card" style="border-top-color:${cor}">
            <div class="comp-pol-header">
              <img class="comp-pol-foto" src="${foto}" alt="${p.nome}" />
              <div>
                <div class="comp-pol-nome">${p.nome}</div>
                <div class="comp-pol-meta">${p.partido} · ${p.uf} · ${p.cargo === 'senador' ? 'Senador(a)' : 'Dep. Federal'}</div>
              </div>
            </div>
            <div class="comp-score-big" style="color:${corScore}">${p.score_geral ?? '—'}<span style="font-size:1rem;color:var(--gray-text)">/10</span></div>
            <div class="comp-metric">
              <span class="comp-metric-label">Presença</span>
              <span class="comp-metric-val">${p.score_presenca != null ? p.score_presenca + '%' : '—'}</span>
              <div class="comp-bar"><div class="comp-bar-fill" style="width:${p.score_presenca||0}%;background:${cor}"></div></div>
            </div>
            <div class="comp-metric">
              <span class="comp-metric-label">Votos registrados</span>
              <span class="comp-metric-val">${p.score_atividade ?? '—'}</span>
              <div class="comp-bar"><div class="comp-bar-fill" style="width:${Math.round((p.score_atividade||0)/maxAtiv*100)}%;background:${cor}"></div></div>
            </div>
            <div class="comp-metric">
              <span class="comp-metric-label">Alinhamento partido</span>
              <span class="comp-metric-val">${p.alinhamento_partido != null ? p.alinhamento_partido + '%' : '—'}</span>
              <div class="comp-bar"><div class="comp-bar-fill" style="width:${p.alinhamento_partido||0}%;background:${cor}"></div></div>
            </div>
            <div class="comp-metric">
              <span class="comp-metric-label">Alinhamento governo</span>
              <span class="comp-metric-val">${p.alinhamento_governo != null ? p.alinhamento_governo + '%' : '—'}</span>
              <div class="comp-bar"><div class="comp-bar-fill" style="width:${p.alinhamento_governo||0}%;background:${cor}"></div></div>
            </div>
            <button class="btn-buscar" style="width:100%;margin-top:10px;font-size:.8rem" onclick="abrirModalPol(${p.id})">Ver perfil completo</button>
          </div>`;
        }).join('')}
      </div>`;
  } catch(e) {
    res.innerHTML = '<div style="padding:20px;color:#dc2626">Erro ao comparar políticos.</div>';
    console.error(e);
  }
}

// ── RANKING POLÍTICOS ──
async function carregarRankingPoliticos() {
  const cargo = document.getElementById('rankPolCargo')?.value || 'senador';
  const uf    = document.getElementById('rankPolUF')?.value || '';
  const ordem = document.getElementById('rankPolOrdem')?.value || 'desc';
  const tbody = document.getElementById('rankPolBody');
  tbody.innerHTML = '<tr><td colspan="5" style="padding:30px;text-align:center"><span class="spinner"></span></td></tr>';

  try {
    let url = `${API}/politicos?cargo=${cargo}&itens=50&pagina=1&ordem_presenca=${ordem}`;
    if (uf) url += `&uf=${uf}`;
    const r    = await fetch(url);
    const data = await r.json();
    const lista = data.dados || [];

    if (!lista.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="padding:20px;text-align:center;color:var(--gray-text)">Nenhum resultado.</td></tr>';
      return;
    }

    tbody.innerHTML = lista.map((p, i) => {
      const presenca  = p.score_presenca  != null ? p.score_presenca + '%' : '—';
      const atividade = p.score_atividade != null ? p.score_atividade : '—';
      const corP = p.score_presenca >= 90 ? '#16a34a' : p.score_presenca >= 70 ? '#ca8a04' : p.score_presenca != null ? '#dc2626' : '#999';
      const pos = i + 1;
      return `<tr onclick="abrirModalPol(${p.id})" style="cursor:pointer">
        <td><div class="rank-pos ${rankClass(pos)}">${pos}</div></td>
        <td><span class="estado-name">${p.nome}</span></td>
        <td><span class="uf-badge">${p.partido || '—'}</span> <span class="uf-badge">${p.uf || '—'}</span></td>
        <td><div class="bar-wrap">
          <div class="bar"><div class="bar-fill" style="width:${p.score_presenca||0}%;background:${corP}"></div></div>
          <span class="bar-num" style="color:${corP}">${presenca}</span>
        </div></td>
        <td><span style="font-weight:700;color:var(--blue)">${atividade}</span> votos</td>
      </tr>`;
    }).join('');
  } catch {
    tbody.innerHTML = '<tr><td colspan="5" style="padding:20px;text-align:center;color:var(--gray-text)">Erro ao carregar ranking.</td></tr>';
  }
}

// ── GOVERNADORES ──
async function carregarGovernadores() {
  try {
    const r = await fetch(`${API}/governadores`);
    const data = await r.json();
    const partidos = [...new Set(data.map(g => g.partido))].sort();
    document.getElementById('govPartidoFiltros').innerHTML =
      `<button class="filter-tab active" onclick="filtrarGov('',this,govData)">Todos</button>` +
      partidos.map(p => `<button class="filter-tab" onclick="filtrarGov('${p}',this,govData)">${p}</button>`).join('');
    govData = data;
    renderGovernadores(data);
  } catch {}
}

function filtrarGov(partido, btn, data) {
  document.querySelectorAll('#govPartidoFiltros .filter-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderGovernadores(partido ? data.filter(g => g.partido === partido) : data);
}

function renderGovernadores(lista) {
  document.getElementById('govGrid').innerHTML = lista.map(g => {
    const foto  = g.foto_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(g.nome)}&background=002776&color=ffdf00&size=80`;
    const score = todosEstados?.find(e => e.uf === g.uf);
    const corScore = score ? scoreColor(score.score) : '#64748b';
    return `<div class="pol-card poder-executivo" onclick="abrirModal('${g.uf}')">
      <img class="pol-foto" src="${foto}" alt="${g.nome}" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(g.nome)}&background=d1fae5&color=065f46&size=80'" />
      <div class="pol-info">
        <span class="poder-badge exe">Executivo · Estado</span>
        <div class="pol-nome" title="${g.nome}">${g.nome}</div>
        <div class="pol-meta">${g.partido || '—'} · ${g.uf || '—'}</div>
        <span class="pol-cargo" style="background:#d1fae5;color:#065f46">Governador(a)</span>
        <div class="pol-score-row" style="margin-top:8px">
          ${score ? `
            <span class="pol-score-item">Score <strong style="color:${corScore}">${score.score}</strong></span>
            <span class="pol-score-item">📚 <strong>${score.educacao}</strong></span>
            <span class="pol-score-item">🏥 <strong>${score.saude}</strong></span>
            <span class="pol-score-item">🔒 <strong>${score.seguranca}</strong></span>
          ` : '<span class="pol-score-item" style="color:#999">Sem score</span>'}
        </div>
      </div>
    </div>`;
  }).join('');
}

async function carregarMinistros() {
  try {
    const r = await fetch(`${API}/ministros`);
    const data = await r.json();
    document.getElementById('minGrid').innerHTML = data.map(m => {
      const foto = m.foto_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(m.nome)}&background=009c3b&color=ffffff&size=80`;
      const orc  = m.orcamento_bi != null
        ? (m.orcamento_bi >= 1000
            ? `R$ ${(m.orcamento_bi/1000).toFixed(1)} tri`
            : `R$ ${m.orcamento_bi.toFixed(1)} bi`)
        : null;
      const exec      = m.execucao_pct != null ? m.execucao_pct : null;
      const execColor = exec != null ? (exec >= 90 ? '#16a34a' : exec >= 75 ? '#ca8a04' : '#dc2626') : '#999';
      const dna = [];
      if (exec != null) dna.push(exec >= 85 ? {l:'Alta eficiência',c:'dna-pos'} : exec >= 70 ? {l:'Eficiência média',c:'dna-neu'} : {l:'Baixa execução',c:'dna-neg'});
      if (orc)          dna.push({l:'Gestor público',c:'dna-neu'});
      const orcNum = m.orcamento_bi || 0;
      if (orcNum >= 100) dna.push({l:'Grande orçamento',c:'dna-pos'});
      return `<div class="pol-card poder-executivo" onclick="abrirModalMinistro(this)"
        data-nome="${m.nome}" data-ministerio="${m.ministerio||''}"
        data-orcamento="${orc||''}" data-execucao="${exec||''}"
        data-destaques="${(m.destaques||'').replace(/"/g,'&quot;')}" data-partido="${m.partido||''}">
        <img class="pol-foto" src="${foto}" alt="${m.nome}" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(m.nome)}&background=d1fae5&color=065f46&size=80'" />
        <div class="pol-info">
          <span class="poder-badge exe">Executivo · Ministério</span>
          <div class="pol-nome" title="${m.nome}">${m.nome}</div>
          <div class="pol-meta" style="font-size:.72rem;line-height:1.3">${m.ministerio || '—'}</div>
          <span class="pol-cargo" style="background:#d1fae5;color:#065f46">Ministro(a)</span>
          <div class="pol-score-row" style="margin-top:8px">
            ${orc  ? `<span class="pol-score-item">💰 <strong>${orc}</strong></span>` : ''}
            ${exec != null ? `<span class="pol-score-item">Exec. <strong style="color:${execColor}">${exec}%</strong></span>` : ''}
          </div>
          ${dna.length ? `<div class="dna-section"><div class="dna-grid">${dna.map(t=>`<span class="dna-tag ${t.c}">${t.l}</span>`).join('')}</div></div>` : ''}
        </div>
      </div>`;
    }).join('');
  } catch(e) { console.error(e); }
}

function abrirModalMinistro(card) {
  const nome       = card.dataset.nome;
  const ministerio = card.dataset.ministerio;
  const orcamento  = card.dataset.orcamento;
  const execucao   = card.dataset.execucao;
  const destaques  = card.dataset.destaques;
  const partido    = card.dataset.partido;
  const execNum    = parseFloat(execucao) || 0;
  const execColor  = execNum >= 90 ? '#16a34a' : execNum >= 75 ? '#ca8a04' : '#dc2626';
  const foto = `https://ui-avatars.com/api/?name=${encodeURIComponent(nome)}&background=009c3b&color=ffffff&size=80`;

  document.getElementById('modalPolFoto').src         = foto;
  document.getElementById('modalPolNome').textContent = nome;
  document.getElementById('modalPolSub').textContent  = `${ministerio} · ${partido || '—'}`;

  const hdr = document.querySelector('#modalPolOverlay .modal-header');
  hdr.className = 'modal-header poder-exe';

  const scoreExec = execNum ? ((execNum / 100) * 10).toFixed(1) : '—';
  const corScore  = execNum >= 85 ? '#16a34a' : execNum >= 70 ? '#ca8a04' : '#dc2626';

  document.getElementById('modalPolScores').innerHTML = `
    <div class="score-item">
      <div class="s-label">📊 Score de Gestão</div>
      <div class="s-val" style="color:${corScore};font-size:1.3rem">${scoreExec}<span style="font-size:.8rem;color:var(--gray-text)"> / 10</span></div>
      <div class="s-bar"><div class="s-bar-fill" style="width:${execNum}%;background:${corScore}"></div></div>
    </div>
    <div class="score-item">
      <div class="s-label">💰 Orçamento Gerenciado</div>
      <div class="s-val" style="color:#009c3b;font-size:1.1rem">${orcamento || '—'}</div>
      <div class="s-bar"><div class="s-bar-fill" style="width:100%;background:#009c3b"></div></div>
    </div>
    <div class="score-item">
      <div class="s-label">📈 Execução Orçamentária</div>
      <div class="s-val" style="color:${execColor}">${execucao ? execucao + '%' : '—'}</div>
      <div class="s-bar"><div class="s-bar-fill" style="width:${execucao||0}%;background:${execColor}"></div></div>
    </div>`;

  document.getElementById('modalPolVotosResumo').innerHTML =
    `<div style="background:var(--gray-bg);border-radius:12px;padding:14px 16px;font-size:.88rem;color:var(--gray-text);line-height:1.7">
      <strong style="color:#009c3b;display:block;margin-bottom:6px">Principais ações e programas:</strong>
      ${(destaques||'Sem informações disponíveis.').split(', ').map(d =>
        `<span style="display:inline-block;background:var(--white);border:1px solid var(--gray-100);border-radius:8px;padding:3px 10px;margin:3px 4px 3px 0;font-size:.8rem">📌 ${d}</span>`
      ).join('')}
    </div>`;

  document.getElementById('modalPolVotacoes').innerHTML = '';
  document.getElementById('modalPolOverlay').classList.add('open');
}

// ── PRESIDENTES ──
const CORES_PARTIDO = {
  PT:'#dc2626', PSDB:'#3b82f6', PL:'#1d4ed8', MDB:'#16a34a',
  PMDB:'#16a34a', PRN:'#9333ea', PSB:'#f59e0b', NOVO:'#ea580c',
};

async function carregarPresidentes() {
  try {
    const r = await fetch(`${API}/presidentes`);
    const data = await r.json();
    const sorted = [...data].sort((a,b) => a.ano_inicio - b.ano_inicio);

    document.getElementById('presTimeline').innerHTML = `
      <div style="position:relative;padding:20px 0">
        <div style="position:absolute;left:50%;top:0;bottom:0;width:3px;background:var(--gray-100);transform:translateX(-50%)"></div>
        ${sorted.map((p, i) => {
          const esq = i % 2 === 0;
          const cor = CORES_PARTIDO[p.partido] || '#64748b';
          const anos = p.ano_fim - p.ano_inicio;
          const ativo = p.ano_fim >= 2025;
          return `<div style="display:flex;justify-content:${esq?'flex-end':'flex-start'};margin-bottom:24px;position:relative">
            <div style="width:46%;${esq?'margin-right:52px':'margin-left:52px'}">
              <div style="background:var(--white);border-radius:16px;padding:18px 20px;box-shadow:var(--shadow);border-left:4px solid ${cor};${ativo?'border:2px solid '+cor:''}">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                  <div style="width:10px;height:10px;border-radius:50%;background:${cor}"></div>
                  <span style="font-size:.72rem;font-weight:700;color:${cor};text-transform:uppercase">${p.partido}</span>
                  ${ativo ? '<span style="font-size:.68rem;background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:10px;font-weight:700">● Atual</span>' : ''}
                </div>
                <div style="font-weight:800;font-size:1rem;color:var(--blue)">${p.nome}</div>
                <div style="font-size:.8rem;color:var(--gray-text);margin-top:4px">${p.ano_inicio} – ${p.ano_fim} · ${anos} ano${anos>1?'s':''}</div>
                <div style="font-size:.78rem;color:var(--gray-text);margin-top:8px;line-height:1.5">${p.bio}</div>
              </div>
            </div>
            <div style="position:absolute;left:50%;transform:translateX(-50%);top:18px;width:14px;height:14px;border-radius:50%;background:${cor};border:3px solid var(--white);box-shadow:0 0 0 3px ${cor}40"></div>
          </div>`;
        }).join('')}
      </div>`;
  } catch {}
}

// ── HISTÓRICO ──
let chartHistorico = null;
const CORES_HIST = ['#002776','#009c3b','#f59e0b','#dc2626','#8b5cf6','#06b6d4'];

async function carregarHistorico() {
  const ufs = document.getElementById('histUFs').value || 'SC,SP,BA,CE';
  const ind  = document.getElementById('histIndicador').value;
  try {
    const r = await fetch(`${API}/historico/comparar/estados?ufs=${encodeURIComponent(ufs)}&indicador=${ind}`);
    const data = await r.json();
    if (!data.length) return;

    const anosSet = new Set();
    data.forEach(e => e.serie.forEach(s => anosSet.add(s.ano)));
    const anos = [...anosSet].sort();

    if (chartHistorico) chartHistorico.destroy();
    chartHistorico = new Chart(document.getElementById('chartHistorico'), {
      type: 'line',
      data: {
        labels: anos,
        datasets: data.map((e, i) => ({
          label: `${e.uf} — ${e.nome}`,
          data: anos.map(a => {
            const s = e.serie.find(x => x.ano === a);
            return s ? s.valor : null;
          }),
          borderColor: CORES_HIST[i % CORES_HIST.length],
          backgroundColor: CORES_HIST[i % CORES_HIST.length] + '20',
          borderWidth: 2.5,
          pointRadius: 4,
          tension: 0.3,
          spanGaps: true,
        }))
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'top' } },
        scales: { y: { beginAtZero: false } }
      }
    });

    document.getElementById('histTabela').innerHTML = `
      <div style="overflow-x:auto">
        <table style="width:100%;border-collapse:collapse;font-size:.88rem">
          <thead>
            <tr style="background:var(--blue);color:white">
              <th style="padding:10px 14px;text-align:left;border-radius:12px 0 0 0">Estado</th>
              ${anos.map((a,i) => `<th style="padding:10px 14px;${i===anos.length-1?'border-radius:0 12px 0 0':''}">${a}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
            ${data.map((e,ri) => `<tr style="border-bottom:1px solid var(--gray-100);${ri%2?'background:var(--gray-bg)':''}">
              <td style="padding:10px 14px;font-weight:700;color:var(--blue)">${e.uf} — ${e.nome}</td>
              ${anos.map(a => {
                const s = e.serie.find(x => x.ano === a);
                return `<td style="padding:10px 14px;text-align:center">${s ? s.valor : '—'}</td>`;
              }).join('')}
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  } catch(err) { console.error(err); }
}

// ── MUNICÍPIOS ──
let munTimer = null;
let chartMunRadar = null;

function debounceMun() {
  clearTimeout(munTimer);
  munTimer = setTimeout(() => carregarMunicipios(1), 400);
}

async function carregarMunicipios(pagina = 1) {
  const uf     = document.getElementById('munUF')?.value     || '';
  const regiao = document.getElementById('munRegiao')?.value || '';
  const ordem  = document.getElementById('munOrdem')?.value  || 'score';
  const busca  = document.getElementById('munBusca')?.value  || '';
  const grid   = document.getElementById('munGrid');
  grid.innerHTML = '<div style="grid-column:1/-1;padding:40px;text-align:center"><span class="spinner"></span> Carregando...</div>';

  try {
    let url = `${API}/municipios?pagina=${pagina}&itens=24&ordem=${ordem}`;
    if (uf)     url += `&uf=${uf}`;
    if (regiao) url += `&regiao=${regiao}`;
    if (busca)  url += `&busca=${encodeURIComponent(busca)}`;

    const r    = await fetch(url);
    const data = await r.json();
    const lista = data.dados || [];

    if (pagina === 1 && !uf && !busca && !regiao) {
      document.getElementById('munTotal').textContent = (data.total || 0).toLocaleString('pt-BR');
      const scores = lista.map(m => m.score).filter(Boolean);
      const med = scores.length ? (scores.reduce((a,b)=>a+b,0)/scores.length).toFixed(1) : '—';
      document.getElementById('munMediaScore').textContent = med;
    }

    if (!lista.length) {
      grid.innerHTML = '<div style="grid-column:1/-1;padding:40px;text-align:center;color:var(--gray-text)">Nenhum município encontrado.</div>';
      return;
    }

    if (pagina === 1) {
      const sorted = [...lista].sort((a,b)=>(b.score||0)-(a.score||0));
      document.getElementById('munMelhor').textContent = sorted[0]?.nome || '—';
      document.getElementById('munPior').textContent   = sorted[sorted.length-1]?.nome || '—';
    }

    grid.innerHTML = lista.map(m => {
      const score = m.score != null ? m.score.toFixed(1) : '—';
      const cor   = m.score >= 70 ? '#16a34a' : m.score >= 50 ? '#ca8a04' : '#dc2626';
      const pop   = m.populacao ? m.populacao.toLocaleString('pt-BR') : '—';
      const regNome = {'N':'Norte','NE':'Nordeste','CO':'Centro-Oeste','SE':'Sudeste','S':'Sul'}[m.regiao] || m.regiao || '—';
      return `<div class="pol-card" style="border-left:4px solid #1a5fb4;cursor:pointer" onclick="abrirModalMunicipio(${m.id})">
        <div style="width:52px;height:52px;border-radius:14px;background:linear-gradient(135deg,#1a5fb4,#003a99);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0">🏙️</div>
        <div class="pol-info">
          <div class="pol-nome" title="${m.nome}">${m.nome}</div>
          <div class="pol-meta">${m.uf} · ${regNome}</div>
          <span class="pol-cargo" style="background:#dbeafe;color:#1a5fb4">Município</span>
          <div class="pol-score-row" style="margin-top:8px">
            <span class="pol-score-item">Score <strong style="color:${cor}">${score}</strong></span>
            <span class="pol-score-item">👥 <strong>${pop}</strong></span>
          </div>
          <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
            ${indicadorMun('📚', 'Edu', m.educacao)}
            ${indicadorMun('🏥', 'Saú', m.saude)}
            ${indicadorMun('🔒', 'Seg', m.seguranca)}
            ${indicadorMun('💰', 'Eco', m.economia)}
          </div>
        </div>
      </div>`;
    }).join('');

    renderPaginacaoMun(data.pagina, data.paginas);
  } catch(e) {
    grid.innerHTML = '<div style="grid-column:1/-1;padding:40px;text-align:center;color:#dc2626">Erro ao carregar municípios.</div>';
    console.error(e);
  }
}

function indicadorMun(icon, label, val) {
  if (val == null) return '';
  const cor = val >= 70 ? '#16a34a' : val >= 50 ? '#ca8a04' : '#dc2626';
  return `<span class="pol-score-item" style="font-size:.7rem">${icon} <strong style="color:${cor}">${val.toFixed(0)}</strong></span>`;
}

function renderPaginacaoMun(atual, total) {
  const el = document.getElementById('munPaginacao');
  if (total <= 1) { el.innerHTML = ''; return; }
  const pages = [];
  for (let i = Math.max(1, atual-2); i <= Math.min(total, atual+2); i++) pages.push(i);
  el.innerHTML = `
    ${atual > 1 ? `<button class="pag-btn" onclick="carregarMunicipios(${atual-1})">‹</button>` : ''}
    ${pages.map(p => `<button class="pag-btn${p===atual?' active':''}" onclick="carregarMunicipios(${p})">${p}</button>`).join('')}
    ${atual < total ? `<button class="pag-btn" onclick="carregarMunicipios(${atual+1})">›</button>` : ''}
    <span style="font-size:.8rem;color:var(--gray-text);margin-left:8px">Página ${atual} de ${total}</span>`;
}

async function abrirModalMunicipio(id) {
  try {
    const r = await fetch(`${API}/municipios/${id}`);
    const m = await r.json();
    const REGIOES_NOME = {N:'Norte',NE:'Nordeste',CO:'Centro-Oeste',SE:'Sudeste',S:'Sul'};

    document.getElementById('modalMunNome').textContent = m.nome;
    document.getElementById('modalMunSub').textContent  =
      `${m.uf} · ${REGIOES_NOME[m.regiao]||m.regiao||'—'} · Pop. ${m.populacao ? m.populacao.toLocaleString('pt-BR') : '—'}`;

    const corScore = m.score >= 70 ? '#16a34a' : m.score >= 50 ? '#ca8a04' : '#dc2626';

    document.getElementById('modalMunScores').innerHTML = [
      { label: '📊 Score Geral', val: m.score,     cor: corScore   },
      { label: '📚 Educação',    val: m.educacao,  cor: '#1a5fb4'  },
      { label: '🏥 Saúde',       val: m.saude,     cor: '#009c3b'  },
      { label: '🔒 Segurança',   val: m.seguranca, cor: '#dc2626'  },
      { label: '💰 Economia',    val: m.economia,  cor: '#f59e0b'  },
    ].map(s => `
      <div class="score-item">
        <div class="s-label">${s.label}</div>
        <div class="s-val" style="color:${s.cor}">${s.val != null ? s.val.toFixed(1) : '—'}</div>
        <div class="s-bar"><div class="s-bar-fill" style="width:${s.val||0}%;background:${s.cor}"></div></div>
      </div>`).join('');

    if (chartMunRadar) chartMunRadar.destroy();
    chartMunRadar = new Chart(document.getElementById('chartMunRadar'), {
      type: 'radar',
      data: {
        labels: ['Educação','Saúde','Segurança','Economia'],
        datasets: [{
          label: m.nome,
          data: [m.educacao||0, m.saude||0, m.seguranca||0, m.economia||0],
          backgroundColor: 'rgba(26,95,180,.15)',
          borderColor: '#1a5fb4',
          borderWidth: 2,
          pointBackgroundColor: '#1a5fb4',
        }]
      },
      options: {
        responsive: true,
        scales: { r: { min:0, max:100, ticks:{ stepSize:20 } } },
        plugins: { legend: { display: false } },
      }
    });

    document.getElementById('modalMunInfo').innerHTML = `
      <div style="background:var(--gray-bg);border-radius:12px;padding:14px 16px;font-size:.85rem;color:var(--gray-text)">
        <strong style="color:var(--blue);display:block;margin-bottom:8px">Informações do Município</strong>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <div>Código IBGE: <strong>${m.codigo_ibge || '—'}</strong></div>
          <div>UF: <strong>${m.uf}</strong></div>
          <div>Região: <strong>${REGIOES_NOME[m.regiao]||m.regiao||'—'}</strong></div>
          <div>Ano ref.: <strong>${m.ano || 2023}</strong></div>
          ${m.area_km2 ? `<div>Área: <strong>${m.area_km2.toLocaleString('pt-BR')} km²</strong></div>` : ''}
        </div>
      </div>`;

    document.getElementById('modalMunOverlay').classList.add('open');
  } catch(e) { console.error(e); }
}

function fecharModalMun(e) {
  if (!e || e.target.id === 'modalMunOverlay') {
    document.getElementById('modalMunOverlay').classList.remove('open');
    if (chartMunRadar) { chartMunRadar.destroy(); chartMunRadar = null; }
  }
}

// ── STF ──
let stfData = [];

function perfilSTF(garantista) {
  if (garantista >= 65) return { label: 'Garantista', cls: 'dna-pos', filtro: 'garantista' };
  if (garantista <= 35) return { label: 'Punitivista', cls: 'dna-neg', filtro: 'punitivista' };
  return { label: 'Equilibrado', cls: 'dna-neu', filtro: 'equilibrado' };
}

function dnaSTF(m) {
  const tags = [];
  const g = m.perfil_garantista ?? 50;
  const p = perfilSTF(g);
  tags.push({ label: p.label, cls: p.cls });

  const julgados = m.processos_julgados || 0;
  if (julgados >= 2000) tags.push({ label: 'Alta atividade', cls: 'dna-pos' });
  else if (julgados < 800) tags.push({ label: 'Baixa atividade', cls: 'dna-neg' });
  else tags.push({ label: 'Atividade média', cls: 'dna-neu' });

  const maioria = m.acompanha_maioria || 0;
  if (maioria >= 80) tags.push({ label: 'Segue maioria', cls: 'dna-neu' });
  else tags.push({ label: 'Independente', cls: 'dna-pos' });

  return tags;
}

function renderSTF(lista) {
  const grid = document.getElementById('stfGrid');
  if (!lista.length) {
    grid.innerHTML = '<div style="grid-column:1/-1;padding:40px;text-align:center;color:var(--gray-text)">Nenhum ministro encontrado.</div>';
    return;
  }

  grid.innerHTML = lista.map(m => {
    const foto       = m.foto_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(m.nome)}&background=7c3aed&color=ffffff&size=80`;
    const score      = m.score_geral != null ? m.score_geral.toFixed(1) : '—';
    const corScore   = m.score_geral >= 7 ? '#16a34a' : m.score_geral >= 5 ? '#ca8a04' : '#dc2626';
    const julgados   = m.processos_julgados ?? '—';
    const maioria    = m.acompanha_maioria  != null ? m.acompanha_maioria + '%' : '—';
    const garantista = m.perfil_garantista  != null ? m.perfil_garantista : null;
    const perfil     = perfilSTF(garantista ?? 50);
    const dna        = dnaSTF(m);
    const indicadoPor = m.indicado_por || '—';

    return `<div class="pol-card poder-judiciario" onclick="abrirModalSTF(${m.id})">
      <img class="pol-foto" src="${foto}" alt="${m.nome}" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(m.nome)}&background=ede9fe&color=7c3aed&size=80'" />
      <div class="pol-info">
        <span class="poder-badge jud">Judiciário · STF</span>
        <div class="pol-nome" title="${m.nome}">${m.nome}</div>
        <div class="pol-meta" style="font-size:.72rem">Indicado: ${indicadoPor} · Posse: ${m.ano_posse || '—'}</div>
        <span class="pol-cargo" style="background:#ede9fe;color:#4c1d95">Ministro(a) STF</span>
        <div class="pol-score-row" style="margin-top:8px">
          <span class="pol-score-item">Score <strong style="color:${corScore}">${score}</strong></span>
          <span class="pol-score-item">⚖️ <strong>${julgados}</strong> proc.</span>
          <span class="pol-score-item">Maioria: <strong>${maioria}</strong></span>
        </div>
        ${garantista !== null ? `
        <div class="perfil-meter" style="margin-top:10px">
          <span style="font-size:.65rem;color:#7c3aed">Garantista</span>
          <div class="perfil-track">
            <div class="perfil-dot" style="left:${garantista}%"></div>
          </div>
          <span style="font-size:.65rem;color:#dc2626">Punitivista</span>
        </div>` : ''}
        <div class="dna-section">
          <h5>DNA</h5>
          <div class="dna-grid">
            ${dna.map(t => `<span class="dna-tag ${t.cls}">${t.label}</span>`).join('')}
          </div>
        </div>
      </div>
    </div>`;
  }).join('');
}

async function carregarSTF() {
  try {
    const r = await fetch(`${API}/stf`);
    stfData = await r.json();
    renderSTF(stfData);
  } catch {
    document.getElementById('stfGrid').innerHTML =
      '<div style="grid-column:1/-1;padding:40px;text-align:center;color:#dc2626">Erro ao carregar ministros do STF.</div>';
  }
}

function filtrarSTF(tipo, btn) {
  document.querySelectorAll('#stfFiltros .filter-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (!tipo) { renderSTF(stfData); return; }
  renderSTF(stfData.filter(m => {
    const g = m.perfil_garantista ?? 50;
    return perfilSTF(g).filtro === tipo;
  }));
}

async function abrirModalSTF(id) {
  const m = stfData.find(x => x.id === id);
  if (!m) return;
  const foto       = m.foto_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(m.nome)}&background=7c3aed&color=ffffff&size=80`;
  const score      = m.score_geral != null ? m.score_geral.toFixed(1) : '—';
  const scoreColor = m.score_geral >= 7 ? '#16a34a' : m.score_geral >= 5 ? '#ca8a04' : '#dc2626';
  const julgados   = m.processos_julgados ?? '—';
  const maioria    = m.acompanha_maioria != null ? m.acompanha_maioria + '%' : '—';
  const garantista = m.perfil_garantista != null ? m.perfil_garantista : null;
  const dna = dnaSTF(m);

  document.getElementById('modalPolFoto').src         = foto;
  document.getElementById('modalPolNome').textContent = m.nome;
  document.getElementById('modalPolSub').textContent  = `STF · Indicado por: ${m.indicado_por || '—'} · Posse: ${m.ano_posse || '—'}`;

  const hdr = document.querySelector('#modalPolOverlay .modal-header');
  hdr.className = 'modal-header poder-jud';

  document.getElementById('modalPolScores').innerHTML = `
    <div class="score-item">
      <div class="s-label">📊 Score Geral</div>
      <div class="s-val" style="color:${scoreColor};font-size:1.4rem">${score}<span style="font-size:.8rem;color:var(--gray-text)"> / 10</span></div>
      <div class="s-bar"><div class="s-bar-fill" style="width:${(m.score_geral||0)*10}%;background:${scoreColor}"></div></div>
    </div>
    <div class="score-item">
      <div class="s-label">⚖️ Processos Julgados</div>
      <div class="s-val" style="color:#7c3aed">${julgados}</div>
      <div class="s-bar"><div class="s-bar-fill" style="width:${Math.min((m.processos_julgados||0)/60,100)}%;background:#7c3aed"></div></div>
    </div>
    <div class="score-item">
      <div class="s-label">🗳️ Acompanha Maioria</div>
      <div class="s-val" style="color:#002776">${maioria}</div>
      <div class="s-bar"><div class="s-bar-fill" style="width:${m.acompanha_maioria||0}%;background:#002776"></div></div>
    </div>
    ${garantista !== null ? `
    <div class="score-item" style="grid-column:1/-1">
      <div class="s-label">⚖️ Perfil Decisório</div>
      <div class="perfil-meter" style="margin-top:8px">
        <span style="font-size:.72rem;font-weight:700;color:#7c3aed">Garantista (${garantista}%)</span>
        <div class="perfil-track" style="flex:1">
          <div class="perfil-dot" style="left:${garantista}%"></div>
        </div>
        <span style="font-size:.72rem;font-weight:700;color:#dc2626">Punitivista (${100-garantista}%)</span>
      </div>
    </div>` : ''}`;

  document.getElementById('modalPolVotosResumo').innerHTML = `
    <div style="background:var(--gray-bg);border-radius:12px;padding:14px 16px;font-size:.88rem;color:var(--gray-text);line-height:1.7">
      <strong style="color:#7c3aed;display:block;margin-bottom:10px">DNA Judicial</strong>
      <div class="dna-grid">
        ${dna.map(t => `<span class="dna-tag ${t.cls}">${t.label}</span>`).join('')}
      </div>
      ${m.bio ? `<p style="margin-top:12px;font-size:.82rem">${m.bio}</p>` : ''}
    </div>
    ${m.casos_destaque ? `
    <div style="background:var(--gray-bg);border-radius:12px;padding:14px 16px;margin-top:10px;font-size:.82rem">
      <strong style="color:#7c3aed;display:block;margin-bottom:8px">🔥 Casos em Destaque</strong>
      ${m.casos_destaque.split(', ').map(c => `<span style="display:inline-block;background:var(--white);border:1px solid #ede9fe;border-radius:8px;padding:3px 10px;margin:3px 4px 3px 0">⚖️ ${c}</span>`).join('')}
    </div>` : ''}`;

  document.getElementById('modalPolVotacoes').innerHTML = `
    <div style="background:var(--gray-bg);border-radius:12px;padding:14px 16px;font-size:.82rem;color:var(--gray-text)">
      Dados de votos individuais em plenário serão integrados na próxima fase (API STF pública).
    </div>`;

  document.getElementById('modalPolOverlay').classList.add('open');
}

// ── INIT ──
function toggleMobileMenu(btn) {
  const menu = document.getElementById('mobileMenu');
  const open = menu.classList.toggle('open');
  if (btn) btn.setAttribute('aria-expanded', open);
}

document.addEventListener('click', function(e) {
  const menu = document.getElementById('mobileMenu');
  const btn  = document.querySelector('.nav-menu-btn');
  if (menu && menu.classList.contains('open') && !menu.contains(e.target) && btn && !btn.contains(e.target)) {
    menu.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  }
});

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    const menu = document.getElementById('mobileMenu');
    const btn  = document.querySelector('.nav-menu-btn');
    if (menu) { menu.classList.remove('open'); }
    if (btn)  { btn.setAttribute('aria-expanded', 'false'); }
  }
});
const FALLBACK = [
  {nome:'Santa Catarina',     uf:'SC',regiao:'S',  educacao:73.3,saude:75.0,seguranca:95.2,economia:40.5,score:77.1},
  {nome:'Paraná',             uf:'PR',regiao:'S',  educacao:68.6,saude:70.0,seguranca:90.5,economia:37.5,score:75.4},
  {nome:'Rio Grande do Sul',  uf:'RS',regiao:'S',  educacao:70.3,saude:72.5,seguranca:91.4,economia:37.5,score:76.5},
  {nome:'São Paulo',          uf:'SP',regiao:'SE', educacao:68.6,saude:67.5,seguranca:97.7,economia:50.0,score:76.8},
  {nome:'Distrito Federal',   uf:'DF',regiao:'CO', educacao:82.9,saude:80.0,seguranca:83.7,economia:73.5,score:82.1},
  {nome:'Minas Gerais',       uf:'MG',regiao:'SE', educacao:60.0,saude:62.5,seguranca:80.2,economia:35.0,score:67.1},
  {nome:'Espírito Santo',     uf:'ES',regiao:'SE', educacao:62.9,saude:55.0,seguranca:66.0,economia:42.5,score:61.5},
  {nome:'Rio de Janeiro',     uf:'RJ',regiao:'SE', educacao:44.3,saude:60.0,seguranca:50.2,economia:42.5,score:51.3},
  {nome:'Goiás',              uf:'GO',regiao:'CO', educacao:54.3,saude:47.5,seguranca:66.5,economia:35.0,score:56.1},
  {nome:'Mato Grosso do Sul', uf:'MS',regiao:'CO', educacao:54.3,saude:55.0,seguranca:65.1,economia:35.0,score:57.9},
];

async function init() {
  const el = document.getElementById('apiStatusHero');
  let online = false;
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(3000) });
    online = r.ok;
  } catch {}

  if (online) {
    el.className = 'api-status online';
    el.innerHTML = '<span class="api-dot"></span> Online';
    const r = await fetch(`${API}/estados`);
    todosEstados = await r.json();
    await carregarResumo();
    carregarStatsPoliticos();
    carregarSenadores(1);
    buscarPoliticos(1);
    carregarGovernadores();
    carregarMinistros();
    carregarSTF();
    carregarMunicipios(1);
    carregarPresidentes();
    carregarHistorico();
    carregarRankingPoliticos();
  } else {
    el.className = 'api-status offline';
    el.innerHTML = '<span class="api-dot"></span> Offline';
    todosEstados = FALLBACK;
    ['pEdu','pSau','pSeg','pEco'].forEach(id => document.getElementById(id).textContent = '—');
  }
  renderRanking(todosEstados);
}

init();
