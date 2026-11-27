const $ = (id) => document.getElementById(id);
let autoIrrigation = true;
let simulatorRunning = true;
let simulatorTimer = null;

$('today').textContent = new Intl.DateTimeFormat('en-IN', {
  weekday: 'long', month: 'long', day: 'numeric', year: 'numeric'
}).format(new Date()).toUpperCase();

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

function setMeter(id, value) {
  $(id).style.width = `${Math.max(0, Math.min(100, Number(value) || 0))}%`;
}

function drawChart(rows, predicted) {
  const actual = rows.slice(-12).map(row => Number(row.soil_moisture));
  if (!actual.length) return;
  const values = [...actual, Number(predicted)];
  const min = Math.max(0, Math.min(...values) - 6);
  const max = Math.min(100, Math.max(...values) + 6);
  const range = Math.max(1, max - min);
  const width = 600, height = 145, pad = 12;
  const point = (value, index, count) => {
    const x = pad + (width - pad * 2) * index / Math.max(1, count - 1);
    const y = height - pad - (height - pad * 2) * (value - min) / range;
    return `${x},${y}`;
  };
  const actualPoints = actual.map((value, i) => point(value, i, actual.length + 1)).join(' ');
  const predictedPoints = `${point(actual.at(-1), actual.length - 1, actual.length + 1)} ${point(predicted, actual.length, actual.length + 1)}`;
  $('chart').innerHTML = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Actual and predicted soil moisture trend"><path d="M ${pad} ${height-pad} H ${width-pad}" stroke="#edf0eb"/><polyline points="${actualPoints}" fill="none" stroke="#4c9561" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><polyline points="${predictedPoints}" fill="none" stroke="#9bab9a" stroke-dasharray="5 5" stroke-width="2"/></svg>`;
}

async function refresh() {
  try {
    const [rows, prediction, status] = await Promise.all([
      api('/api/readings?limit=40'), api('/api/prediction'), api('/api/status')
    ]);
    if (!rows.length) return;
    const latest = rows.at(-1);
    $('moisture').innerHTML = `${Number(latest.soil_moisture).toFixed(1)}<small>%</small>`;
    $('temperature').innerHTML = `${Number(latest.temperature).toFixed(1)}<small>°C</small>`;
    $('humidity').innerHTML = `${Number(latest.humidity).toFixed(1)}<small>%</small>`;
    $('light').innerHTML = `${Number(latest.light).toFixed(1)}<small>%</small>`;
    $('water').textContent = `${Number(latest.water_level).toFixed(1)}%`;
    setMeter('moistureBar', latest.soil_moisture);
    setMeter('waterBar', latest.water_level);
    $('moistureHint').textContent = Number(latest.soil_moisture) < 30 ? 'Below the demo irrigation threshold' : 'Above the demo irrigation threshold';
    $('pumpText').textContent = status.pump_on ? 'Pump ON · simulated' : 'Pump OFF · simulated';
    $('pumpDot').style.color = status.pump_on ? '#72a85b' : '#9aa49d';
    $('pumpSub').textContent = status.water_level === 'low' ? 'Water tank level is too low' : status.pump_on ? 'AI prediction recommends irrigation' : 'Irrigation is not currently recommended';
    const predicted = Number(prediction.predicted_moisture);
    $('forecast').textContent = `Predicted soil moisture in 30 minutes: ${predicted.toFixed(1)}% · Recommendation: ${prediction.recommendation.replace('_', ' ').toUpperCase()}`;
    $('insight').textContent = prediction.recommendation === 'irrigate' ? 'Irrigation is recommended.' : prediction.recommendation === 'water_low' ? 'Water level is too low for irrigation.' : 'Soil moisture is expected to remain sufficient.';
    $('insightText').textContent = `Random Forest Regression predicts ${predicted.toFixed(1)}% soil moisture in 30 minutes using the latest five sensor readings. This is a model trained on synthetic demonstration data.`;
    drawChart(rows, predicted);
  } catch (error) {
    $('forecast').textContent = 'Cannot reach the application. Start the server and reload this page.';
  }
}

async function sendSimulatedReading() {
  try {
    await api('/api/demo-reading', { method: 'POST' });
    await refresh();
  } catch (error) {
    console.error(error);
  }
}

function startSimulator() {
  if (simulatorTimer) clearInterval(simulatorTimer);
  simulatorRunning = true;
  $('sampleBtn').textContent = 'Ⅱ Pause sensor simulator';
  $('sampleBtn').classList.add('primary');
  sendSimulatedReading();
  simulatorTimer = setInterval(sendSimulatedReading, 10000);
}

function stopSimulator() {
  simulatorRunning = false;
  if (simulatorTimer) clearInterval(simulatorTimer);
  simulatorTimer = null;
  $('sampleBtn').textContent = '▶ Start sensor simulator';
}

$('sampleBtn').addEventListener('click', () => simulatorRunning ? stopSimulator() : startSimulator());
$('autoBtn').addEventListener('click', async () => {
  autoIrrigation = !autoIrrigation;
  await api(`/api/mode?enabled=${autoIrrigation}`, { method: 'POST' });
  $('autoBtn').textContent = autoIrrigation ? '● Auto irrigation on' : '○ Auto irrigation off';
  $('autoBtn').classList.toggle('off', !autoIrrigation);
  refresh();
});

refresh();
startSimulator();
setInterval(refresh, 4000);
