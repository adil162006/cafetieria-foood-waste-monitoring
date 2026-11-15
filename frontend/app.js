const colors = ['#287353', '#d5a348', '#7699a8', '#927fae', '#d0785e', '#87a879'];
const charts = new Map();
const number = (value, digits = 0) => Number(value ?? 0).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
const setText = (id, value) => { document.getElementById(id).textContent = value; };
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const dateLabel = value => { const d = new Date(`${value}T00:00:00`); return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' }); };

async function api(path) {
  const response = await fetch(path, { headers: { Accept: 'application/json' } });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function showError(message) {
  const banner = document.getElementById('error-banner');
  banner.textContent = message;
  banner.hidden = false;
}

function hideError() {
  const banner = document.getElementById('error-banner');
  banner.hidden = true;
  banner.textContent = '';
}

function makeChart(canvasId, type, data, options) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !window.Chart) {
    const parent = canvas?.parentElement;
    if (parent) parent.innerHTML = '<div class="chart-error">Interactive charts need an internet connection to load Chart.js.</div>';
    return;
  }
  charts.get(canvasId)?.destroy();
  charts.set(canvasId, new Chart(canvas, { type, data, options }));
}

const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 450 },
  plugins: {
    legend: { display: false },
    tooltip: { backgroundColor: '#19372b', padding: 11, cornerRadius: 8, titleFont: { family: 'DM Sans', weight: '600' }, bodyFont: { family: 'DM Sans' } }
  },
  scales: {
    x: { grid: { display: false }, border: { display: false }, ticks: { color: '#849087', maxTicksLimit: 7, maxRotation: 0, font: { family: 'DM Sans', size: 10 } } },
    y: { beginAtZero: true, border: { display: false, dash: [3, 4] }, grid: { color: '#edf1ed' }, ticks: { color: '#849087', font: { family: 'DM Sans', size: 10 } } }
  }
};

function renderDashboard(data) {
  hideError();
  const kpi = data.kpis || {};
  setText('kpi-waste', `${number(kpi.total_waste, 1)} kg`);
  setText('kpi-meals', number(kpi.total_meals));
  setText('kpi-per-meal', `${number(kpi.waste_per_meal, 3)} kg`);
  setText('kpi-categories', number(data.categories.length));
  setText('updated-at', `Updated ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`);
  setText('daily-row-count', `${number(data.daily.length)} days`);

  const daily = data.daily || [];
  makeChart('daily-chart', 'line', {
    labels: daily.map(row => dateLabel(row.waste_date)),
    datasets: [{ label: 'Food waste', data: daily.map(row => Number(row.total_food_waste_kg)), borderColor: colors[0], backgroundColor: 'rgba(40,115,83,.12)', borderWidth: 2, fill: true, tension: .28, pointRadius: 0, pointHoverRadius: 5 }]
  }, { ...commonOptions, interaction: { intersect: false, mode: 'index' }, plugins: { ...commonOptions.plugins, tooltip: { ...commonOptions.plugins.tooltip, callbacks: { label: item => ` ${number(item.raw, 2)} kg` } } }, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, ticks: { ...commonOptions.scales.y.ticks, callback: value => `${number(value)} kg` } } } });

  const categories = data.categories || [];
  makeChart('category-chart', 'doughnut', {
    labels: categories.map(row => row.waste_category),
    datasets: [{ data: categories.map(row => Number(row.total_food_waste_kg)), backgroundColor: colors, borderColor: '#fff', borderWidth: 4, hoverOffset: 7 }]
  }, { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, pointStyle: 'circle', padding: 16, color: '#65756a', font: { family: 'DM Sans', size: 10 } } }, tooltip: { ...commonOptions.plugins.tooltip, callbacks: { label: item => ` ${item.label}: ${number(item.raw, 2)} kg` } } } });

  const monthly = data.monthly || [];
  makeChart('monthly-chart', 'bar', {
    labels: monthly.map(row => new Date(`${row.waste_month}T00:00:00`).toLocaleDateString(undefined, { month: 'short', year: '2-digit' })),
    datasets: [{ label: 'Food waste', data: monthly.map(row => Number(row.total_food_waste_kg)), backgroundColor: monthly.map((_, i) => i === monthly.length - 1 ? colors[0] : '#afd0ba'), borderRadius: 5, maxBarThickness: 20 }]
  }, { ...commonOptions, plugins: { ...commonOptions.plugins, tooltip: { ...commonOptions.plugins.tooltip, callbacks: { label: item => ` ${number(item.raw, 2)} kg` } } }, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, ticks: { ...commonOptions.scales.y.ticks, callback: value => `${number(value)} kg` } } } });

  const recent = [...daily].reverse().slice(0, 50);
  document.getElementById('daily-table').innerHTML = recent.length ? recent.map(row => `<tr><td>${escapeHtml(dateLabel(row.waste_date))}</td><td class="number">${number(row.total_food_waste_kg, 2)} kg</td><td class="number">${number(row.total_meals_served)}</td><td class="number">${number(row.average_food_waste_per_meal_kg, 3)} kg</td><td class="number">${row.average_temperature_c == null ? '—' : `${number(row.average_temperature_c, 1)} °C`}</td><td class="number">${number(row.record_count)}</td></tr>`).join('') : '<tr><td colspan="6" class="empty-cell">No analytics rows found.</td></tr>';
}

function renderAnswerChart(result) {
  const frame = document.getElementById('answer-chart');
  const rows = result.rows || [];
  if (rows.length < 1) { frame.hidden = true; return; }
  frame.hidden = false;
  const id = result.id;
  if (id === 'demand_relation' || id === 'temperature_relation') {
    const xKey = id === 'demand_relation' ? 'total_meals_served' : 'average_temperature_c';
    makeChart('answer-canvas', 'scatter', {
      datasets: [{ label: 'Daily food waste', data: rows.map(row => ({ x: Number(row[xKey]), y: Number(row.total_food_waste_kg) })), backgroundColor: 'rgba(40,115,83,.65)', pointRadius: 4, pointHoverRadius: 7 }]
    }, { ...commonOptions, scales: { x: { ...commonOptions.scales.x, title: { display: true, text: id === 'demand_relation' ? 'Meals served' : 'Average temperature (°C)', color: '#748278', font: { family: 'DM Sans' } } }, y: { ...commonOptions.scales.y, title: { display: true, text: 'Food waste (kg)', color: '#748278', font: { family: 'DM Sans' } } } } });
    return;
  }
  const dateKey = id === 'daily_waste' ? 'waste_date' : 'waste_month';
  const categoryKey = id === 'highest_category' ? 'waste_category' : dateKey;
  const valueKey = Object.keys(rows[0]).find(key => key.includes('food_waste') && !key.includes('per_meal'));
  if (!valueKey) { frame.hidden = true; return; }
  const labels = rows.map(row => categoryKey === 'waste_category' ? row[categoryKey] : dateLabel(row[categoryKey]));
  const chartType = id === 'daily_waste' ? 'line' : 'bar';
  makeChart('answer-canvas', chartType, { labels, datasets: [{ label: 'Food waste (kg)', data: rows.map(row => Number(row[valueKey])), borderColor: colors[0], backgroundColor: chartType === 'line' ? 'rgba(40,115,83,.12)' : colors[0], borderWidth: 2, fill: chartType === 'line', tension: .25, pointRadius: chartType === 'line' ? 0 : 3, borderRadius: chartType === 'bar' ? 4 : 0 }] }, { ...commonOptions, indexAxis: id === 'highest_category' ? 'y' : 'x', interaction: { intersect: false, mode: 'index' } });
}

function renderAnswerTable(rows) {
  const root = document.getElementById('answer-table');
  if (!rows.length) { root.innerHTML = '<p class="empty-cell">No rows matched this question.</p>'; return; }
  const keys = Object.keys(rows[0]);
  root.innerHTML = `<table><thead><tr>${keys.map(key => `<th>${escapeHtml(key.replaceAll('_', ' ').toUpperCase())}</th>`).join('')}</tr></thead><tbody>${rows.slice(0,100).map(row => `<tr>${keys.map(key => `<td>${escapeHtml(typeof row[key] === 'number' ? number(row[key], 3) : row[key])}</td>`).join('')}</tr>`).join('')}</tbody></table>${rows.length > 100 ? `<p class="row-count">Showing first 100 of ${number(rows.length)} rows.</p>` : ''}`;
}

async function loadDashboard() {
  const button = document.getElementById('refresh-button');
  button.disabled = true;
  document.querySelector('.main-content').classList.add('loading');
  try { renderDashboard(await api('/api/dashboard')); }
  catch (error) { showError(error.message); setText('updated-at', 'Warehouse unavailable'); }
  finally { button.disabled = false; document.querySelector('.main-content').classList.remove('loading'); }
}

async function loadQuestions() {
  const { questions } = await api('/api/questions');
  const select = document.getElementById('question-select');
  select.insertAdjacentHTML('beforeend', questions.map(question => `<option value="${escapeHtml(question.id)}">${escapeHtml(question.label)}</option>`).join(''));
}

async function askQuestion() {
  const select = document.getElementById('question-select');
  const button = document.getElementById('ask-button');
  if (!select.value) { select.focus(); return; }
  button.disabled = true;
  button.innerHTML = 'Querying…';
  try {
    const result = await api(`/api/question?id=${encodeURIComponent(select.value)}`);
    document.getElementById('answer-area').hidden = false;
    setText('answer-title', result.label);
    setText('answer-sql', result.sql);
    renderAnswerTable(result.rows);
    renderAnswerChart(result);
  } catch (error) { showError(error.message); }
  finally { button.disabled = false; button.innerHTML = 'Get answer <span>→</span>'; }
}

document.getElementById('refresh-button').addEventListener('click', loadDashboard);
document.getElementById('ask-button').addEventListener('click', askQuestion);
loadQuestions().catch(error => showError(error.message));
loadDashboard();
