export function esc(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[c]); }
export function stateText(t, state) { try { return t(`resource.state.${state ?? 'UNKNOWN'}`); } catch { return String(state ?? 'UNKNOWN'); } }
export function unit(t, name) { try { return t(`resource.unit.${name}`); } catch { return String(name ?? ''); } }
export function bytes(t, value) {
  if (!Number.isFinite(value)) return stateText(t, 'UNAVAILABLE');
  if (Math.abs(value) < 1024 ** 2) return t('resource.format.numberUnit', { value: value.toLocaleString(), unit: unit(t, 'bytes') });
  const name = Math.abs(value) >= 1024 ** 3 ? 'GiB' : 'MiB';
  return t('resource.format.numberUnit', { value: (value / (name === 'GiB' ? 1024 ** 3 : 1024 ** 2)).toFixed(1), unit: unit(t, name) });
}
export function metricValue(t, metric) {
  if (metric?.state !== 'PRESENT' || !Number.isFinite(metric.value)) return stateText(t, 'UNAVAILABLE');
  const value = metric.value;
  switch (metric.units) {
    case 'bytes': return bytes(t, value);
    case 'fraction': return t('resource.format.percent', { value: (100 * value).toFixed(1) });
    case 'percent': return t('resource.format.percent', { value: value.toFixed(1) });
    case 'ms': return t('resource.format.numberUnit', { value: value.toFixed(0), unit: unit(t, 'ms') });
    case 'USD': return t('resource.format.money', { value: value.toFixed(2) });
    default: return metric.units ? t('resource.format.numberUnit', { value: value.toLocaleString(), unit: unit(t, metric.units) }) : t('resource.format.number', { value: value.toLocaleString() });
  }
}
export function badge(t, value, semantic = false) {
  const state = value ?? 'UNKNOWN', type = semantic ? 'semantic' : 'state';
  return `<span class="resource-${type}" data-resource-${type}="${esc(String(state).toLowerCase().replaceAll('_', '-'))}">${esc(stateText(t, state))}</span>`;
}
