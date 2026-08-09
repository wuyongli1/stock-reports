// 足球竞彩分析展示页交互
// 数据：../data/calibration.json（累计统计）+ ../data/predictions/YYYY-MM-DD.json（单日）
const DATA = '../data';
let calib = null;
let allMatches = [];   // 所有预测比赛（扁平化，带日期）
let dailyMap = {};     // date -> 完整单日数据
let currentFilter = 'ALL';

const $ = id => document.getElementById(id);

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error('404 ' + url);
  return r.json();
}

function fmtPct(x) {
  if (x == null || isNaN(x)) return '-';
  return (x * 100).toFixed(1) + '%';
}
function fmtOdds(x) {
  if (x == null) return '-';
  return Number(x).toFixed(2);
}

async function init() {
  try {
    calib = await fetchJson(`${DATA}/calibration.json`);
  } catch (e) {
    $('lastUpdated').textContent = '暂无数据（首次发布，等待首次分析）';
    $('predHint').textContent = '尚无预测记录。每日 11:30 自动分析后此处更新。';
    return;
  }
  renderStats(calib);
  renderParlay(calib);
  renderFilters(calib);
  $('lastUpdated').textContent = calib.last_updated
    ? `最近更新：${calib.last_updated}`
    : '暂无更新';

  // 并发拉取最近 20 天预测
  const dates = (calib.daily_index || []).slice(0, 20);
  if (dates.length === 0) {
    $('predHint').textContent = '尚无预测记录。每日 11:30 自动分析后此处更新。';
    return;
  }
  const results = await Promise.all(
    dates.map(d => fetchJson(`${DATA}/predictions/${d}.json`).catch(() => null))
  );
  allMatches = [];
  results.filter(Boolean).forEach(p => {
    dailyMap[p.date] = p;
    (p.matches || []).forEach(m => allMatches.push({ ...m, _date: p.date }));
  });
  renderTable();
}

function renderStats(c) {
  const hit = c.hit_rate || 0;
  const roi = c.roi || 0;
  const cards = [
    { v: c.settled || 0, l: '已结算场次' },
    { v: fmtPct(hit), l: '命中率', cls: hit >= 0.5 ? 'win' : '' },
    { v: (roi >= 0 ? '+' : '') + fmtPct(roi), l: 'ROI', cls: roi >= 0 ? 'win' : 'lose' },
    { v: c.brier_score != null ? c.brier_score.toFixed(3) : '-', l: 'Brier Score' },
    { v: c.total_predictions || 0, l: '总预测场次' },
  ];
  $('statsGrid').innerHTML = cards.map(s =>
    `<div class="stat-card"><div class="v ${s.cls || ''}">${s.v}</div><div class="l">${s.l}</div></div>`
  ).join('');
}

function renderParlay(c) {
  const pr = c.parlay_record || {};
  if (!pr.total) {
    $('parlayBox').innerHTML = '<p class="hint">暂无串关记录</p>';
    return;
  }
  const hit = pr.hit_rate || 0;
  const roi = pr.roi || 0;
  $('parlayBox').innerHTML = `
    <div class="parlay-row">
      <span>总串关 <b>${pr.total}</b></span>
      <span>命中 <b style="color:var(--win)">${pr.won}</b></span>
      <span>命中率 <b>${fmtPct(hit)}</b></span>
      <span>ROI <b style="color:${roi>=0?'var(--win)':'var(--lose)'}">${roi>=0?'+':''}${fmtPct(roi)}</b></span>
      <span>总投入 ¥${pr.total_stake || 0} · 总回收 ¥${pr.total_return || 0}</span>
    </div>`;
}

function renderFilters(c) {
  const leagues = Object.keys(c.by_league || {}).sort();
  const tags = ['全部', ...leagues];
  $('leagueFilter').innerHTML = tags.map(t =>
    `<button class="${t === '全部' ? 'active' : ''}" onclick="setFilter('${t}')">${t}</button>`
  ).join('');
}

function setFilter(t) {
  currentFilter = t === '全部' ? 'ALL' : t;
  document.querySelectorAll('.league-filter button').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  renderTable();
}

function renderTable() {
  let list = allMatches.slice().sort((a, b) => (b._date || '').localeCompare(a._date || ''));
  if (currentFilter !== 'ALL') {
    list = list.filter(m => m.league === currentFilter);
  }
  if (list.length === 0) {
    $('predBody').innerHTML = '';
    $('predHint').textContent = '当前筛选无记录';
    return;
  }
  $('predBody').innerHTML = list.map(m => {
    const res = m.status || 'pending';
    const resCls = res === 'correct' ? 'result-win' : res === 'wrong' ? 'result-lose' : 'result-pending';
    const resTxt = res === 'correct' ? '✓ 命中' : res === 'wrong' ? '✗ 未中' : '待结算';
    const conf = m.confidence || 'low';
    const mp = m.model_prob || {};
    return `<tr onclick="showDetail('${m._date}')">
      <td>${m._date || '-'}</td>
      <td class="league">${m.league || '-'}</td>
      <td>${m.home || ''} vs ${m.away || ''}</td>
      <td>${(m.kickoff || '').slice(11, 16) || '-'}</td>
      <td class="prob-cell">${fmtPct(mp.home_win)}</td>
      <td class="rec">${m.recommendation || '-'}</td>
      <td>${m.value_market || '-'}</td>
      <td class="conf-${conf}">${conf}</td>
      <td class="${resCls}">${resTxt}</td>
    </tr>`;
  }).join('');
  $('predHint').textContent = `共 ${list.length} 场 · 点击行查看单日详情`;
}

function showDetail(date) {
  const p = dailyMap[date];
  if (!p) return;
  $('detailTitle').textContent = `${date} 单日分析详情`;
  let html = '';
  // 昨日复盘
  if (p.review_of_yesterday && Object.keys(p.review_of_yesterday).length) {
    const r = p.review_of_yesterday;
    html += `<div class="review-box"><b>📋 昨日复盘</b><br>
      昨日预测 ${r.total || 0} 场，命中 ${r.correct || 0} 场，命中率 ${fmtPct(r.hit_rate)}；
      串关 ${r.parlay_total || 0} 单命中 ${r.parlay_won || 0} 单。
      ${r.note || ''}</div>`;
  }
  // 各场
  (p.matches || []).forEach(m => {
    const mp = m.model_prob || {};
    const mk = m.market_fair_prob || {};
    const ev = m.ev || {};
    const lo = m.lottery_odds || {};
    const had = lo.had || {};
    const hhad = lo.hhad || {};
    const scores = m.topline_score_prob || [];
    html += `<div class="match-block">
      <div class="match-head">
        <div><span class="lg">${m.league || ''}</span> <span class="teams">${m.home} vs ${m.away}</span></div>
        <div class="hint">开赛 ${(m.kickoff || '').slice(11, 16)} · ${m.matchId || ''}</div>
      </div>
      <div class="prob-bar">
        <div class="prob-h" style="width:${(mp.home_win||0)*100}%">主胜 ${fmtPct(mp.home_win)}</div>
        <div class="prob-d" style="width:${(mp.draw||0)*100}%">平 ${fmtPct(mp.draw)}</div>
        <div class="prob-a" style="width:${(mp.away_win||0)*100}%">客胜 ${fmtPct(mp.away_win)}</div>
      </div>
      <div class="match-grid">
        <div class="mg"><span class="k">市场公平概率</span><br><span class="vv">主${fmtPct(mk.home_win)} 平${fmtPct(mk.draw)} 客${fmtPct(mk.away_win)}</span></div>
        <div class="mg"><span class="k">主胜 EV</span><br><span class="vv" style="color:${(ev.home_win||0)>=0?'var(--win)':'var(--lose)'}">${fmtPct(ev.home_win)}</span></div>
        <div class="mg"><span class="k">体彩胜平负赔率</span><br><span class="vv">${fmtOdds(had.h)}/${fmtOdds(had.d)}/${fmtOdds(had.a)}</span></div>
        <div class="mg"><span class="k">让球</span><br><span class="vv">${hhad.goalLine || '-'} (${fmtOdds(hhad.h)}/${fmtOdds(hhad.d)}/${fmtOdds(hhad.a)})</span></div>
        <div class="mg"><span class="k">推荐</span><br><span class="vv rec">${m.recommendation || '-'}</span></div>
        <div class="mg"><span class="k">置信度</span><br><span class="vv conf-${m.confidence||'low'}">${m.confidence || '-'}</span></div>
      </div>
      ${scores.length ? `<div class="match-grid"><div class="mg"><span class="k">最可能比分</span><br><span class="vv">${scores.slice(0,5).map(s=>`${s[0]}(${fmtPct(s[1])})`).join(' · ')}</span></div></div>` : ''}
    </div>`;
  });
  // 串关
  if (p.parlays && p.parlays.length) {
    html += '<h3 style="margin:16px 0 8px">串关建议</h3>';
    p.parlays.forEach(pl => {
      const legs = (pl.legs || []).map(l => `<div class="leg">• ${l.match} → <b>${l.pick}</b> @ ${fmtOdds(l.odds)} (模型概率 ${fmtPct(l.model_prob)})</div>`).join('');
      html += `<div class="parlay-detail">
        <h4>${pl.type} ${pl.result ? `<span class="parlay-tag ${pl.result==='won'?'won':'lost'}">${pl.result==='won'?'命中':'未中'}</span>` : ''}</h4>
        ${legs}
        <div class="leg" style="margin-top:6px">联合概率 ${fmtPct(pl.combined_prob)} · 联合赔率 ${fmtOdds(pl.combined_odds)} · EV ${fmtPct(pl.ev)} · 全损概率 ${fmtPct(pl.all_loss_prob)}</div>
      </div>`;
    });
  }
  $('detailBody').innerHTML = html;
  $('detailCard').hidden = false;
  window.scrollTo(0, 0);
}

function hideDetail() {
  $('detailCard').hidden = true;
}

init();
