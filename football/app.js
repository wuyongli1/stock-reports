const labels = {
  identity_or_data: "赛事身份或数据错误",
  stale_lineup_or_injury: "阵容 / 伤停信息过期",
  model_misspecification: "模型或先验设定偏差",
  settlement_misunderstanding: "玩法结算理解错误",
  event_randomness: "红牌 / 点球等随机事件",
  right_direction_bad_price: "方向正确但价格不佳",
  right_result_weak_process: "结果正确但过程薄弱"
};

const fmtPercent = value => value == null ? "—" : `${(value * 100).toFixed(1)}%`;
const fmtNumber = value => value == null ? "—" : Number(value).toFixed(3);
const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
})[char]);

function renderMetrics(summary) {
  const metrics = [
    ["已建立会话", summary.sessions, "按体彩比赛编号日期归档"],
    ["官方赛事快照", summary.fixtures, "保留全部可售玩法和抓取时间"],
    ["核心选择命中率", fmtPercent(summary.primary_hit_rate), `${summary.settled_primary} 个已结算核心选择`],
    ["1X2 平均 Brier", fmtNumber(summary.mean_1x2_brier), "越低表示概率校准越好"]
  ];
  document.getElementById("metric-grid").innerHTML = metrics.map(([label, value, context]) => `
    <article class="metric">
      <div class="metric-label">${escapeHtml(label)}</div>
      <div class="metric-value">${escapeHtml(value)}</div>
      <div class="metric-context">${escapeHtml(context)}</div>
    </article>`).join("");
  document.getElementById("sample-note").textContent =
    `稳定优势声明门槛：至少 ${summary.stable_edge_sample_threshold} 个同类已结算样本；当前 ${summary.comparable_1x2_samples} 个。`;
}

function renderTrend(sessions) {
  const usable = sessions.filter(item => item.primary_settled > 0 || item.mean_brier != null);
  const target = document.getElementById("trend-chart");
  if (!usable.length) {
    target.innerHTML = '<div class="empty-chart">完成至少一次赛后复盘后显示趋势。</div>';
    return;
  }
  const width = 1000, height = 310, left = 54, right = 34, top = 24, bottom = 48;
  const plotW = width - left - right, plotH = height - top - bottom;
  const x = index => left + (usable.length === 1 ? plotW / 2 : index * plotW / (usable.length - 1));
  const y = value => top + (1 - value) * plotH;
  const hitPoints = usable.map((item, index) => ({
    x: x(index), y: y(item.primary_settled ? item.primary_hits / item.primary_settled : 0),
    visible: item.primary_settled > 0
  })).filter(item => item.visible);
  const brierPoints = usable.map((item, index) => ({
    x: x(index), y: y(item.mean_brier == null ? 0 : Math.min(item.mean_brier / 2, 1)),
    visible: item.mean_brier != null
  })).filter(item => item.visible);
  const line = points => points.map((point, index) => `${index ? "L" : "M"}${point.x},${point.y}`).join(" ");
  const grids = [0, .25, .5, .75, 1].map(value => `
    <line class="grid" x1="${left}" y1="${y(value)}" x2="${width - right}" y2="${y(value)}"></line>
    <text class="axis-label" x="${left - 10}" y="${y(value) + 4}" text-anchor="end">${Math.round(value * 100)}%</text>`).join("");
  const dates = usable.map((item, index) => `
    <text class="axis-label" x="${x(index)}" y="${height - 16}" text-anchor="middle">${escapeHtml(item.date.slice(5))}</text>`).join("");
  target.innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">
    ${grids}${dates}
    ${hitPoints.length > 1 ? `<path class="hit-line" d="${line(hitPoints)}"></path>` : ""}
    ${brierPoints.length > 1 ? `<path class="brier-line" d="${line(brierPoints)}"></path>` : ""}
    ${hitPoints.map(point => `<circle class="hit-point" cx="${point.x}" cy="${point.y}" r="5"></circle>`).join("")}
    ${brierPoints.map(point => `<rect class="brier-point" x="${point.x - 4}" y="${point.y - 4}" width="8" height="8" rx="2"></rect>`).join("")}
  </svg>`;
}

function pill(status) {
  const complete = status === "complete";
  return `<span class="pill ${complete ? "complete" : "pending"}">${escapeHtml(status)}</span>`;
}

function renderSessions(sessions) {
  const body = document.getElementById("session-body");
  const empty = document.getElementById("empty-state");
  if (!sessions.length) {
    body.innerHTML = "";
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  body.innerHTML = [...sessions].reverse().map(item => `
    <tr>
      <td class="num">${escapeHtml(item.date)}</td>
      <td class="num">${item.fixtures}</td>
      <td>${pill(item.analysis_status)}</td>
      <td class="num">${item.primary} / ${item.observe}</td>
      <td class="num">${item.results}</td>
      <td class="num">${item.primary_settled ? `${item.primary_hits}/${item.primary_settled}` : "—"}</td>
      <td class="num">${fmtNumber(item.mean_brier)}</td>
      <td>${pill(item.review_status)}</td>
    </tr>`).join("");
}

function renderErrors(errors) {
  const target = document.getElementById("error-bars");
  if (!errors.length) {
    target.innerHTML = '<div class="empty-state"><p>尚无已归类错误。</p><span>复盘积累后，这里会显示最常见的过程问题。</span></div>';
    return;
  }
  const maximum = Math.max(...errors.map(item => item.count), 1);
  target.innerHTML = errors.map(item => `
    <div class="error-row">
      <div class="error-name">${escapeHtml(labels[item.name] || item.name)}</div>
      <div class="error-track"><div class="error-fill" style="width:${item.count / maximum * 100}%"></div></div>
      <div class="error-count">${item.count}</div>
    </div>`).join("");
}

async function loadDashboard() {
  try {
    let data = window.__DASHBOARD_DATA__;
    if (!data) {
      const response = await fetch("data.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      data = await response.json();
    }
    renderMetrics(data.summary);
    renderTrend(data.sessions);
    renderSessions(data.sessions);
    renderErrors(data.error_classes);
    document.getElementById("generated-at").textContent = `数据更新 ${data.generated_at.replace("T", " ")}`;
    document.getElementById("notice").textContent = data.notice;
  } catch (error) {
    document.getElementById("generated-at").textContent = "数据读取失败";
    document.getElementById("metric-grid").innerHTML = '<div class="empty-state"><p>无法读取看板数据。</p><span>请先运行 python scripts\\football_lab.py dashboard。</span></div>';
    console.error(error);
  }
}

loadDashboard();
