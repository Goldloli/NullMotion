// Applies hand-made HyperFrames drafts from public/references/hand/<id>.json onto the local
// drafts.json / sections.json (both git-ignored). Each hand file:
//   { "bg": "#111", "sections": [[name, start, [[absTime, kind, text, options], ...]], ...] }
// Beat times are absolute seconds in the film; they become per-section `at` offsets, and the
// entry is marked `hand: true` so batch redraws leave it alone. Re-run any time.
import fs from 'node:fs';
const DIR = new URL('../public/references/', import.meta.url);
const read = name => JSON.parse(fs.readFileSync(new URL(name, DIR), 'utf8'));
const drafts = read('drafts.json'), sections = read('sections.json');
const catalog = await fetch('http://127.0.0.1:4343/api/references').then(r => r.json()).then(r => r.references).catch(() => []);
let count = 0;
for (const file of fs.readdirSync(new URL('hand/', DIR)).filter(f => f.endsWith('.json'))) {
  const id = file.slice(0, -5), spec = read('hand/' + file);
  const end = spec.end ?? catalog.find(r => r.id === id)?.duration;
  if (!end) { console.warn('skip (no duration)', id); continue; }
  drafts.drafts[id] = { hand: true, palette: { bg: spec.bg || '#111111', fg: '#f4f4f4', accent: '#ffffff' },
    sections: spec.sections.map(([name, start, beats]) => ({ name, beats: beats.map(([t, kind, text = '', o = {}]) => [kind, text, { ...o, at: +Math.max(0, t - start).toFixed(2) }]) })) };
  sections[id] = spec.sections.map(([, start], i) => ({ start, end: spec.sections[i + 1]?.[1] ?? end }));
  count++;
}
fs.writeFileSync(new URL('drafts.json', DIR), JSON.stringify(drafts) + '\n');
fs.writeFileSync(new URL('sections.json', DIR), JSON.stringify(sections) + '\n');
console.log(`applied ${count} hand drafts`);
