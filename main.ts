// News Image 24 November 2026 — entrypoint (Node 22, standard library only).
//
// The image is pre-rendered by draw_news24.py into entry.png beside this file.
// This program only copies those exact bytes to the output directory: no
// network, no randomness, no drawing at run time, so repeated runs are
// byte-identical and the gate sees exactly the bytes committed in the repo.
//
// Run locally the way the grader does:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, 'entry.png');
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const target = join(outDir, 'entry.png');

if (!existsSync(source)) {
  throw new Error(`entry.png missing next to main.ts (looked in ${source})`);
}

mkdirSync(outDir, { recursive: true });
copyFileSync(source, target);

const bytes = statSync(target).size;
if (bytes > 1048576) {
  throw new Error(`entry.png is ${bytes} bytes, over the 1 MiB gate`);
}

// The grader runs this program twice and compares bytes: prove the copy is
// exact by hashing both sides before reporting success.
const digest = (p) => createHash('sha256').update(readFileSync(p)).digest('hex');
const srcHash = digest(source);
if (digest(target) !== srcHash) {
  throw new Error(`copied entry.png does not match ${source} (sha256 mismatch)`);
}

console.log(`wrote ${target} (${bytes} bytes, sha256 ${srcHash})`);
