import type { ParentConfig, WordState } from './types';
import { DEFAULT_CONFIG } from './types';

const KEY_SCORE = 'wordkeys:score';
const KEY_EXPOSURE = 'wordkeys:exposure';
const KEY_CONFIG = 'wordkeys:config';
const KEY_GLOBAL_COUNT = 'wordkeys:globalCount';

export function loadScore(): number {
  const raw = localStorage.getItem(KEY_SCORE);
  const n = raw === null ? 0 : Number(raw);
  return Number.isFinite(n) && n >= 0 ? Math.floor(n) : 0;
}

export function saveScore(score: number): void {
  localStorage.setItem(KEY_SCORE, String(score));
}

export function loadExposure(): Map<string, WordState> {
  try {
    const raw = localStorage.getItem(KEY_EXPOSURE);
    if (!raw) return new Map();
    const obj = JSON.parse(raw) as Record<string, WordState>;
    const map = new Map<string, WordState>();
    for (const [word, s] of Object.entries(obj)) {
      if (
        typeof s === 'object' &&
        s !== null &&
        Number.isFinite(s.exposureCount) &&
        Number.isFinite(s.nextEligibleAt)
      ) {
        map.set(word, { exposureCount: s.exposureCount, nextEligibleAt: s.nextEligibleAt });
      }
    }
    return map;
  } catch {
    return new Map();
  }
}

export function saveExposure(states: Map<string, WordState>): void {
  localStorage.setItem(KEY_EXPOSURE, JSON.stringify(Object.fromEntries(states)));
}

/**
 * Global pick counter (PRD §4.4). Persisted alongside exposure states so
 * cooldowns (nextEligibleAt) keep their meaning across sessions and remounts.
 */
export function loadGlobalCount(): number {
  const raw = localStorage.getItem(KEY_GLOBAL_COUNT);
  const n = raw === null ? 0 : Number(raw);
  return Number.isFinite(n) && n >= 0 ? Math.floor(n) : 0;
}

export function saveGlobalCount(count: number): void {
  localStorage.setItem(KEY_GLOBAL_COUNT, String(count));
}

export function loadConfig(): ParentConfig {
  try {
    const raw = localStorage.getItem(KEY_CONFIG);
    if (!raw) return { ...DEFAULT_CONFIG };
    const obj = JSON.parse(raw) as Partial<ParentConfig>;
    return {
      roundSize:
        Number.isInteger(obj.roundSize) && (obj.roundSize as number) >= 1
          ? (obj.roundSize as number)
          : DEFAULT_CONFIG.roundSize,
      readChinese: typeof obj.readChinese === 'boolean' ? obj.readChinese : DEFAULT_CONFIG.readChinese,
      rate: obj.rate === 0.6 || obj.rate === 0.9 ? obj.rate : DEFAULT_CONFIG.rate,
    };
  } catch {
    return { ...DEFAULT_CONFIG };
  }
}

export function saveConfig(config: ParentConfig): void {
  localStorage.setItem(KEY_CONFIG, JSON.stringify(config));
}
