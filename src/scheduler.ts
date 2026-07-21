import type { WordEntry, WordState } from './types';

/**
 * Exposure scheduling per PRD §4.4:
 * exposure count + increasing-interval cooldown + priority-weighted random,
 * with a "thaw the nearest-eligible word" fallback so a keypress always responds.
 */

export function initialState(): WordState {
  return { exposureCount: 0, nextEligibleAt: 0 };
}

export function isEligible(state: WordState, globalCount: number): boolean {
  return state.exposureCount === 0 || state.nextEligibleAt <= globalCount;
}

/**
 * Weighted-random pick among eligible words of a letter pool.
 * Falls back to the word closest to becoming eligible when all are cooling.
 * Returns null only when the pool itself is empty.
 */
export function pickWord(
  pool: WordEntry[],
  states: Map<string, WordState>,
  globalCount: number,
  random: () => number = Math.random,
): WordEntry | null {
  if (pool.length === 0) return null;

  const eligible = pool.filter((w) =>
    isEligible(states.get(w.word) ?? initialState(), globalCount),
  );

  if (eligible.length === 0) {
    // All cooling: thaw the one closest to eligible (ties: higher priority first).
    return pool.reduce((best, w) => {
      const s = states.get(w.word) ?? initialState();
      const b = states.get(best.word) ?? initialState();
      if (s.nextEligibleAt !== b.nextEligibleAt) {
        return s.nextEligibleAt < b.nextEligibleAt ? w : best;
      }
      return w.priority > best.priority ? w : best;
    });
  }

  const totalWeight = eligible.reduce((sum, w) => sum + w.priority, 0);
  let roll = random() * totalWeight;
  for (const w of eligible) {
    roll -= w.priority;
    if (roll < 0) return w;
  }
  return eligible[eligible.length - 1];
}

/**
 * Record one exposure: bump count and set the next cooldown from the
 * configured interval sequence (index capped at the last interval).
 * Returns the updated state (caller persists it).
 */
export function recordExposure(
  state: WordState,
  globalCount: number,
  intervals: number[],
): WordState {
  const exposureCount = state.exposureCount + 1;
  const interval = intervals[Math.min(exposureCount - 1, intervals.length - 1)] ?? 3;
  return { exposureCount, nextEligibleAt: globalCount + interval };
}
