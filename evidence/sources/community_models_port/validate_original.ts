// Validation harness: bundles the ORIGINAL MagnusPladsen TypeScript model (commit 68faa86) and prints preset top areas + theory %.
// Run: mkdir /tmp/v && cd /tmp/v && npm i esbuild@0.23.1 && npx esbuild <this file> --bundle --platform=node --outfile=out.js --alias:@=/home/user/test/data/raw/magnus/src && node out.js
// Output must match run_model.py / teorier_port.py (verified 2026-09-25: identical top areas and percentages).
import { beregn, FORHAND, toppOmrader, utelukkNokkel } from '@/lib/modell'
import { posisjonerRundtPeking } from '@/lib/fly'
import { sannsynligheter, standardBevis } from '@/data/teorier'
import * as fs from 'fs'
const R = '/home/user/test/data/raw/magnus/public/data/'
const dt = JSON.parse(fs.readFileSync(R + 'drivetime.json', 'utf8'))
const fly = JSON.parse(fs.readFileSync(R + 'fly_2130.json', 'utf8'))
const inn = JSON.parse(fs.readFileSync(R + 'innlandet.json', 'utf8'))
const ute = JSON.parse(fs.readFileSync(R + 'utelukket.json', 'utf8'))
const punkter = dt.punkter.map(([lat, lon, sek, meter, snap]: number[]) => ({ lat, lon, sek, meter, snap }))
const ktx = {
  flyPos: posisjonerRundtPeking(fly),
  innlandet: inn.geometry.coordinates.map((poly: number[][][]) => poly[0].map(([lon, lat]) => [lat, lon])),
  utelukket: new Set(ute.celler.map(([la, lo]: number[]) => utelukkNokkel(la, lo))),
}
console.log('flyPos', ktx.flyPos.length)
for (const f of FORHAND) {
  const res = beregn(punkter, f.vekter, ktx as any)
  const t = toppOmrader(punkter, res)
  const n9 = Array.from(res.relativ).filter((x) => x >= 0.9).length
  console.log(f.id, 'n>=0.9', n9, t.map((i) => `${punkter[i].lat},${punkter[i].lon}(${res.relativ[i].toFixed(3)})`).join(' '))
}
for (const m of ['alt', 'hint'] as const) {
  const p = sannsynligheter(standardBevis(m))
  console.log(m, Object.entries(p).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v.toFixed(2)}`).join(', '))
}
