const form = document.querySelector('#estimateForm');
const chatForm = document.querySelector('#chatForm');
const drawingForm = document.querySelector('#drawingForm');
const fields = ['length_m', 'width_m', 'beam_spacing_m', 'panel_run_m', 'wall_panel_length_m', 'bearing_depth_m', 'fiber_dosage_bags_m2'];
let currentInput = null;

function number(id) { return Number(document.getElementById(id).value); }
function inputPayload(save = true) {
  const payload = Object.fromEntries(fields.map((id) => [id, number(id)]));
  payload.room_name = document.querySelector('#room_name').value || 'Room';
  payload.save = save;
  return payload;
}
function fmt(value, digits = 0) { return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits }); }
function showError(message = '') { const el = document.querySelector('#formError'); el.textContent = message; el.classList.toggle('hidden', !message); }

function drawSlab(result) {
  const svg = document.querySelector('#slabSvg');
  const spanIsLength = result.span_orientation === 'length';
  const slabW = spanIsLength ? 450 : 260;
  const slabH = spanIsLength ? 250 : 310;
  const x = (640 - slabW) / 2, y = (360 - slabH) / 2;
  const beamLines = Array.from({ length: result.beam_count }, (_, i) => {
    const ratio = result.beam_count === 1 ? 0 : i / (result.beam_count - 1);
    return spanIsLength
      ? `<line class="beam" x1="${x}" y1="${y + ratio * slabH}" x2="${x + slabW}" y2="${y + ratio * slabH}"/><text class="beam-label" x="${x - 30}" y="${y + ratio * slabH + 4}">B${i + 1}</text>`
      : `<line class="beam" x1="${x + ratio * slabW}" y1="${y}" x2="${x + ratio * slabW}" y2="${y + slabH}"/><text class="beam-label" x="${x + ratio * slabW - 7}" y="${y - 10}">B${i + 1}</text>`;
  }).join('');
  const panelLines = Array.from({ length: result.panels_per_bay - 1 }, (_, i) => spanIsLength
    ? `<line class="panel-line" x1="${x + ((i + 1) / result.panels_per_bay) * slabW}" y1="${y}" x2="${x + ((i + 1) / result.panels_per_bay) * slabW}" y2="${y + slabH}"/>`
    : `<line class="panel-line" x1="${x}" y1="${y + ((i + 1) / result.panels_per_bay) * slabH}" x2="${x + slabW}" y2="${y + ((i + 1) / result.panels_per_bay) * slabH}"/>`).join('');
  svg.innerHTML = `<rect class="bearing" x="${x - 10}" y="${y - 10}" width="${slabW + 20}" height="${slabH + 20}"/><rect fill="#1d2b41" x="${x}" y="${y}" width="${slabW}" height="${slabH}"/>${panelLines}${beamLines}<text class="dimension" x="320" y="345" text-anchor="middle">Span ${fmt(result.span_m, 2)} m | Distribution ${fmt(result.distribution_m, 2)} m</text>`;
}
function render(result) {
  document.querySelector('#beamCount').textContent = fmt(result.beam_count);
  document.querySelector('#beamLm').textContent = fmt(result.total_beam_linear_meters, 2);
  document.querySelector('#panelOrder').textContent = fmt(result.panels_to_order);
  document.querySelector('#panelBuffer').textContent = `${fmt(result.panel_buffer)} panel site buffer`;
  document.querySelector('#wallPanelOrder').textContent = fmt(result.wall_panels_to_order);
  document.querySelector('#wallPanelBuffer').textContent = `${fmt(result.wall_panel_buffer)} panel site buffer`;
  document.querySelector('#fiberBags').textContent = fmt(result.fiber_bags);
  document.querySelector('#grossArea').textContent = `${fmt(result.gross_screed_area_m2, 2)} m2 gross area`;
  document.querySelector('#span').textContent = `${fmt(result.span_m, 2)} m`;
  document.querySelector('#distribution').textContent = `${fmt(result.distribution_m, 2)} m`;
  document.querySelector('#bays').textContent = fmt(result.bay_count);
  document.querySelector('#theoreticalPanels').textContent = fmt(result.theoretical_panels);
  document.querySelector('#orientation').textContent = `T-beams span the shorter ${result.span_orientation} dimension`;
  drawSlab(result);
}
async function calculate(save = true) {
  const payload = inputPayload(save);
  if (fields.some((id) => !Number.isFinite(payload[id]) || payload[id] < 0) || payload.length_m <= 0 || payload.width_m <= 0) { showError('Enter valid positive room and module dimensions.'); return null; }
  showError();
  const response = await fetch('/api/v1/estimate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!response.ok) { const error = await response.json(); throw new Error(error.detail?.[0]?.msg || 'Calculation could not be completed.'); }
  const data = await response.json(); currentInput = data.inputs; render(data.result);
  document.querySelector('#estimateId').textContent = data.result.saved_estimate_id ? `Estimate #${data.result.saved_estimate_id} saved` : '';
  return data;
}
form.addEventListener('submit', async (event) => { event.preventDefault(); try { await calculate(true); } catch (error) { showError(error.message); } });
document.querySelector('#resetButton').addEventListener('click', () => { form.reset(); document.querySelector('#length_m').value = 5; document.querySelector('#width_m').value = 4; document.querySelector('#room_name').value = 'Room 01'; calculate(false).catch((error) => showError(error.message)); });
function addMessage(text, kind) { const node = document.createElement('div'); node.className = kind === 'user' ? 'user-msg' : 'assistant-msg'; node.textContent = text; document.querySelector('#chatLog').append(node); node.parentElement.scrollTop = node.parentElement.scrollHeight; }
chatForm.addEventListener('submit', async (event) => { event.preventDefault(); const input = document.querySelector('#chatInput'); const message = input.value.trim(); if (!message) return; addMessage(message, 'user'); input.value = ''; try { const response = await fetch('/api/v1/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, estimate_input: currentInput ? { ...currentInput, save: false } : null }) }); const data = await response.json(); if (!response.ok) throw new Error('Assistant unavailable.'); addMessage(data.answer, 'assistant'); if (data.estimate) render(data.estimate); } catch (error) { addMessage(error.message, 'assistant'); } });

drawingForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const file = document.querySelector('#drawingFile').files[0];
  const status = document.querySelector('#drawingStatus');
  const results = document.querySelector('#drawingResults');
  const button = document.querySelector('#drawingButton');
  if (!file) return;
  status.textContent = 'Reading dimensions locally… this may take a minute.';
  results.classList.add('hidden'); button.disabled = true;
  try {
    const body = new FormData(); body.append('upload', file);
    const response = await fetch('/api/v1/drawing/analyse', { method: 'POST', body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Drawing analysis failed.');
    status.textContent = `${data.rooms.length} room(s): ${fmt(data.total_t_beams)} T-beams (${fmt(data.total_beam_linear_meters, 2)} m), ${fmt(data.total_panels_to_order)} 1 m slab panels and ${fmt(data.total_wall_panels_to_order)} 3 m wall panels. Review dimensions before ordering.`;
    results.innerHTML = data.rooms.length
      ? `<div class="drawing-warning">AI interpretation — totals include a 10% allowance. Confirm openings and shared walls against the issued drawing.</div>${data.rooms.map(({ room, estimate }) => `<button class="drawing-room" data-length="${room.length_m}" data-width="${room.width_m}" data-name="${room.name}"><span>${room.name}: ${fmt(room.length_m, 2)} × ${fmt(room.width_m, 2)} m (${Math.round(room.confidence * 100)}% confidence)</span><b>${fmt(estimate.beam_count)} T-beams · ${fmt(estimate.panels_to_order)} slab · ${fmt(estimate.wall_panels_to_order)} wall</b><small>${room.evidence || 'No evidence supplied'} · Click to load</small></button>`).join('')}`
      : '<div class="drawing-warning">No explicitly dimensioned rooms were found. Upload a clearer export or enter dimensions manually.</div>';
    results.classList.remove('hidden');
    results.querySelectorAll('.drawing-room').forEach((item) => item.addEventListener('click', () => {
      document.querySelector('#length_m').value = item.dataset.length;
      document.querySelector('#width_m').value = item.dataset.width;
      document.querySelector('#room_name').value = item.dataset.name;
      calculate(false).catch((error) => showError(error.message));
    }));
  } catch (error) { status.textContent = error.message; }
  finally { button.disabled = false; }
});
calculate(false).catch((error) => showError(error.message));
