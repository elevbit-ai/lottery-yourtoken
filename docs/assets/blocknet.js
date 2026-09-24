/*
 * Blockz10 Neural — JavaScript mirror of the Python reference
 * (src/blockz10_neural/blocknet.py). Pure ES module, no dependencies;
 * runs in any modern browser and in Node >= 18.
 *
 * The network IS the Block 15/5 pyramid: 16 blocks, N rounds of
 *   1. conservative redistribution  x <- T x   (column-softmax weights)
 *   2. threshold bonus              a = u + g * relu(u - mean(u))
 * and the class is read at the BASE of the pyramid (blocks 11..15).
 *
 * Author : Joaquim Pedro de Morais Filho <j360074@hotmail.com>
 * License: MIT
 */

export const N = 16;
export const LEVELS = [[0], [1], [2, 3], [4, 5, 6], [7, 8, 9, 10],
                       [11, 12, 13, 14, 15]];
export const BASE_IDX = LEVELS[5];
export const INPUT_IDX = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
export const FLOOR = 0.02;

/* ---------- input encoding ---------- */

// features: array of B arrays of D numbers in [0,1]. Returns X[16][B].
export function encodeInput(features) {
  const B = features.length, D = features[0].length;
  if (D > INPUT_IDX.length) throw new Error("at most 10 features");
  const X = Array.from({ length: N }, () => new Float64Array(B).fill(FLOOR));
  for (let d = 0; d < D; d++)
    for (let b = 0; b < B; b++) X[INPUT_IDX[d]][b] = FLOOR + features[b][d];
  for (let b = 0; b < B; b++) {
    let s = 0;
    for (let i = 0; i < N; i++) s += X[i][b];
    for (let i = 0; i < N; i++) X[i][b] /= s;
  }
  return X;
}

/* ---------- the network ---------- */

export class BlockNet {
  constructor(nClasses, rounds = 3, gain = 1.0, seed = 155) {
    this.C = nClasses;
    this.R = rounds;
    this.g = gain;
    const rng = mulberry32(seed);
    this.thetas = Array.from({ length: rounds }, () =>
      Array.from({ length: N }, () =>
        Float64Array.from({ length: N }, () => gauss(rng) * 0.3)));
    this.scale = 20.0;
    this.bias = new Float64Array(nClasses);
  }

  static fromDict(d) {
    const net = new BlockNet(d.n_classes, d.rounds, d.gain);
    net.thetas = d.thetas.map((t) => t.map((row) => Float64Array.from(row)));
    net.scale = d.scale;
    net.bias = Float64Array.from(d.bias);
    return net;
  }

  toDict() {
    return {
      format: "blockz10-neural/1",
      n_classes: this.C, rounds: this.R, gain: this.g,
      scale: this.scale, bias: [...this.bias],
      thetas: this.thetas.map((t) => t.map((r) => [...r])),
    };
  }

  // Column-softmax of each round's theta (columns sum to 1 exactly).
  matrices() {
    return this.thetas.map((th) => {
      const T = Array.from({ length: N }, () => new Float64Array(N));
      for (let j = 0; j < N; j++) {
        let mx = -Infinity;
        for (let i = 0; i < N; i++) if (th[i][j] > mx) mx = th[i][j];
        let s = 0;
        for (let i = 0; i < N; i++) { T[i][j] = Math.exp(th[i][j] - mx); s += T[i][j]; }
        for (let i = 0; i < N; i++) T[i][j] /= s;
      }
      return T;
    });
  }

  // X: [16][B]. Returns {logits, xs, us, ms} (xs = states per round, for viz).
  forward(X, trace = false) {
    const Ts = this.matrices();
    const B = X[0].length;
    const xs = [X], us = [], ms = [];
    let x = X;
    for (const T of Ts) {
      const u = matmul(T, x);
      const m = Array.from({ length: N }, () => new Float64Array(B));
      const a = Array.from({ length: N }, () => new Float64Array(B));
      for (let b = 0; b < B; b++) {
        let mean = 0;
        for (let i = 0; i < N; i++) mean += u[i][b];
        mean /= N;
        for (let i = 0; i < N; i++) {
          const over = u[i][b] > mean;
          m[i][b] = over ? 1 : 0;
          a[i][b] = u[i][b] + (over ? this.g * (u[i][b] - mean) : 0);
        }
      }
      us.push(u); ms.push(m); xs.push(a);
      x = a;
    }
    const logits = Array.from({ length: this.C }, () => new Float64Array(B));
    for (let c = 0; c < this.C; c++)
      for (let b = 0; b < B; b++)
        logits[c][b] = this.scale * x[BASE_IDX[c]][b] + this.bias[c];
    return trace ? { logits, xs, us, ms } : { logits };
  }

  predict(features) {
    const { logits } = this.forward(encodeInput(features));
    const B = features.length, out = [];
    for (let b = 0; b < B; b++) {
      let best = 0;
      for (let c = 1; c < this.C; c++) if (logits[c][b] > logits[best][b]) best = c;
      out.push(best);
    }
    return out;
  }

  lossAndGrads(X, y) {
    const B = X[0].length;
    const { logits, xs, us, ms } = this.forward(X, true);
    const Ts = this.matrices();

    // softmax + cross-entropy
    const P = Array.from({ length: this.C }, () => new Float64Array(B));
    let loss = 0;
    for (let b = 0; b < B; b++) {
      let mx = -Infinity;
      for (let c = 0; c < this.C; c++) if (logits[c][b] > mx) mx = logits[c][b];
      let s = 0;
      for (let c = 0; c < this.C; c++) { P[c][b] = Math.exp(logits[c][b] - mx); s += P[c][b]; }
      for (let c = 0; c < this.C; c++) P[c][b] /= s;
      loss -= Math.log(P[y[b]][b] + 1e-12);
    }
    loss /= B;

    const G = P;
    for (let b = 0; b < B; b++) G[y[b]][b] -= 1;
    for (let c = 0; c < this.C; c++) for (let b = 0; b < B; b++) G[c][b] /= B;

    const xK = xs[xs.length - 1];
    let gradScale = 0;
    const gradBias = new Float64Array(this.C);
    let dX = Array.from({ length: N }, () => new Float64Array(B));
    for (let c = 0; c < this.C; c++) {
      for (let b = 0; b < B; b++) {
        gradScale += G[c][b] * xK[BASE_IDX[c]][b];
        gradBias[c] += G[c][b];
        dX[BASE_IDX[c]][b] = this.scale * G[c][b];
      }
    }

    const gradThetas = new Array(this.R);
    for (let r = this.R - 1; r >= 0; r--) {
      const m = ms[r], xPrev = xs[r], T = Ts[r];
      // through a = u + g*m*(u - mean(u))
      const gradU = Array.from({ length: N }, () => new Float64Array(B));
      for (let b = 0; b < B; b++) {
        let sum = 0;
        for (let i = 0; i < N; i++) sum += m[i][b] * dX[i][b];
        for (let i = 0; i < N; i++)
          gradU[i][b] = dX[i][b] + this.g * (m[i][b] * dX[i][b] - sum / N);
      }
      const gradT = matmulBt(gradU, xPrev);          // gradU @ xPrev^T
      dX = matmulAt(T, gradU);                       // T^T @ gradU
      // through the column-softmax
      const gth = Array.from({ length: N }, () => new Float64Array(N));
      for (let j = 0; j < N; j++) {
        let dot = 0;
        for (let i = 0; i < N; i++) dot += T[i][j] * gradT[i][j];
        for (let i = 0; i < N; i++) gth[i][j] = T[i][j] * (gradT[i][j] - dot);
      }
      gradThetas[r] = gth;
    }
    return { loss, gradThetas, gradScale, gradBias };
  }

  /**
   * Full-batch momentum SGD, mirroring BlockNet.train in Python.
   * onStep(step, loss) is called every `every` steps; if it returns a
   * Promise it is awaited (lets a UI animate the loss curve).
   */
  async train(features, labels, { steps = 3000, lr = 0.6, momentum = 0.9,
                                  onStep = null, every = 50 } = {}) {
    const X = encodeInput(features);
    const velT = this.thetas.map((t) => t.map(() => new Float64Array(N)));
    let velS = 0;
    const velB = new Float64Array(this.C);
    const history = [];
    for (let step = 0; step < steps; step++) {
      const { loss, gradThetas, gradScale, gradBias } = this.lossAndGrads(X, labels);
      for (let r = 0; r < this.R; r++)
        for (let i = 0; i < N; i++)
          for (let j = 0; j < N; j++) {
            velT[r][i][j] = momentum * velT[r][i][j] - lr * gradThetas[r][i][j];
            this.thetas[r][i][j] += velT[r][i][j];
          }
      velS = momentum * velS - lr * gradScale;
      this.scale += velS;
      for (let c = 0; c < this.C; c++) {
        velB[c] = momentum * velB[c] - lr * gradBias[c];
        this.bias[c] += velB[c];
      }
      history.push(loss);
      if (onStep && (step % every === 0 || step === steps - 1))
        await onStep(step, loss);
    }
    return history;
  }

  accuracy(features, labels) {
    const p = this.predict(features);
    let hit = 0;
    for (let i = 0; i < labels.length; i++) if (p[i] === labels[i]) hit++;
    return hit / labels.length;
  }
}

/* ---------- linear algebra helpers ---------- */

function matmul(T, X) {            // (N,N) @ (N,B)
  const B = X[0].length;
  const out = Array.from({ length: N }, () => new Float64Array(B));
  for (let i = 0; i < N; i++)
    for (let k = 0; k < N; k++) {
      const t = T[i][k];
      if (t === 0) continue;
      const row = X[k], o = out[i];
      for (let b = 0; b < B; b++) o[b] += t * row[b];
    }
  return out;
}

function matmulAt(T, X) {          // T^T @ X : (N,N)^T @ (N,B)
  const B = X[0].length;
  const out = Array.from({ length: N }, () => new Float64Array(B));
  for (let k = 0; k < N; k++)
    for (let i = 0; i < N; i++) {
      const t = T[k][i];
      if (t === 0) continue;
      const row = X[k], o = out[i];
      for (let b = 0; b < B; b++) o[b] += t * row[b];
    }
  return out;
}

function matmulBt(A, X) {          // A @ X^T : (N,B) @ (B,N) -> (N,N)
  const B = A[0].length;
  const out = Array.from({ length: N }, () => new Float64Array(N));
  for (let i = 0; i < N; i++)
    for (let j = 0; j < N; j++) {
      let s = 0;
      for (let b = 0; b < B; b++) s += A[i][b] * X[j][b];
      out[i][j] = s;
    }
  return out;
}

/* ---------- deterministic RNG (for fresh nets in the browser) ---------- */

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function gauss(rng) {              // Box-Muller
  let u = 0, v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

/* ---------- the three tasks ---------- */

export function xorData() {
  return { features: [[0, 0], [0, 1], [1, 0], [1, 1]], labels: [0, 1, 1, 0] };
}

export function bzEncodeLen(s) {
  let out = 0, i = 0;
  while (i < s.length) {
    let j = i;
    while (j < s.length && s[j] === s[i]) j++;
    const run = j - i;
    out += s[i] === "e" ? Math.floor(run / 9) + (run % 9 ? 1 : 0) : run;
    i = j;
  }
  return out;
}

export function patternFeatures(s) {
  const n = s.length, runs = [];
  let i = 0;
  while (i < n) {
    let j = i;
    while (j < n && s[j] === s[i]) j++;
    runs.push(j - i);
    i = j;
  }
  const maxRun = Math.max(...runs);
  const meanRun = runs.reduce((a, b) => a + b, 0) / runs.length;
  let e = 0;
  for (const c of s) if (c === "e") e++;
  return [runs.length / n, maxRun / n, Math.min(meanRun / 10, 1),
          bzEncodeLen(s) / n, e / n, (runs.length - 1) / (n - 1)];
}

const STAY = [0.93, 0.12, 0.50];
export const PATTERN_NAMES = ["blocos/runs", "alternado/alternating", "aleatório/random"];

export function makeString(cls, length, rng = Math.random) {
  const out = [rng() < 0.5 ? "e" : "1"];
  for (let k = 1; k < length; k++)
    out.push(rng() < STAY[cls] ? out[k - 1] : (out[k - 1] === "e" ? "1" : "e"));
  return out.join("");
}

export function patternData(nPerClass, length = 64, seed = 155) {
  const rng = mulberry32(seed);
  const features = [], labels = [], strings = [];
  for (let c = 0; c < 3; c++)
    for (let k = 0; k < nPerClass; k++) {
      const s = makeString(c, length, rng);
      features.push(patternFeatures(s));
      labels.push(c);
      strings.push(s);
    }
  return { features, labels, strings };
}

// IRIS: pass the raw rows [sl, sw, pl, pw, class]; returns normalized split.
// With `fixedSplit` ({train:[idx], test:[idx]}) it reproduces the exact
// stratified split used by the Python suite (so accuracies match).
export function irisData(rows, trainPerClass = 40, seed = 155, fixedSplit = null) {
  const mins = [Infinity, Infinity, Infinity, Infinity];
  const maxs = [-Infinity, -Infinity, -Infinity, -Infinity];
  for (const r of rows)
    for (let d = 0; d < 4; d++) {
      if (r[d] < mins[d]) mins[d] = r[d];
      if (r[d] > maxs[d]) maxs[d] = r[d];
    }
  const norm = (r) => r.slice(0, 4).map((v, d) => (v - mins[d]) / (maxs[d] - mins[d]));
  const train = { features: [], labels: [] }, test = { features: [], labels: [] };
  if (fixedSplit) {
    for (const i of fixedSplit.train) {
      train.features.push(norm(rows[i]));
      train.labels.push(rows[i][4]);
    }
    for (const i of fixedSplit.test) {
      test.features.push(norm(rows[i]));
      test.labels.push(rows[i][4]);
    }
    return { train, test, mins, maxs };
  }
  const rng = mulberry32(seed);
  for (let c = 0; c < 3; c++) {
    const idx = rows.map((r, i) => [r[4], i]).filter(([cc]) => cc === c).map(([, i]) => i);
    for (let i = idx.length - 1; i > 0; i--) {           // Fisher-Yates
      const j = Math.floor(rng() * (i + 1));
      [idx[i], idx[j]] = [idx[j], idx[i]];
    }
    idx.forEach((i, k) => {
      const dst = k < trainPerClass ? train : test;
      dst.features.push(norm(rows[i]));
      dst.labels.push(c);
    });
  }
  return { train, test, mins, maxs };
}
