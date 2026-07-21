import { describe, expect, it } from 'vitest';
import type { WordEntry, WordState } from './types';
import { initialState, isEligible, pickWord, recordExposure } from './scheduler';

const INTERVALS = [3, 6, 12, 24, 48];

function makeWord(word: string, priority = 100): WordEntry {
  return {
    word,
    letter: word[0],
    matchType: 'initial',
    priority,
    zh: word,
    image: `images/${word}.png`,
  };
}

/** Deterministic PRNG (mulberry32) for reproducible tests. */
function mulberry32(seed: number): () => number {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

describe('exposure scheduler (PRD §4.4)', () => {
  it('treats never-exposed words as always eligible', () => {
    expect(isEligible(initialState(), 0)).toBe(true);
    expect(isEligible({ exposureCount: 1, nextEligibleAt: 4 }, 3)).toBe(false);
    expect(isEligible({ exposureCount: 1, nextEligibleAt: 4 }, 4)).toBe(true);
  });

  it('applies the increasing interval sequence, capped at the last value', () => {
    let s = initialState();
    s = recordExposure(s, 1, INTERVALS);
    expect(s).toEqual({ exposureCount: 1, nextEligibleAt: 4 }); // +3
    s = recordExposure(s, 10, INTERVALS);
    expect(s).toEqual({ exposureCount: 2, nextEligibleAt: 16 }); // +6
    s.exposureCount = 5;
    s = recordExposure(s, 100, INTERVALS);
    expect(s).toEqual({ exposureCount: 6, nextEligibleAt: 148 }); // capped at 48
  });

  it('AC-F006-01: a word in cooldown is not re-selected while others are eligible', () => {
    const apple = makeWord('apple');
    const ant = makeWord('ant');
    const pool = [apple, ant];
    const states = new Map<string, WordState>([
      ['apple', { exposureCount: 1, nextEligibleAt: 100 }], // cooling
      ['ant', initialState()],
    ]);
    for (let i = 0; i < 50; i++) {
      expect(pickWord(pool, states, 1, mulberry32(i))?.word).toBe('ant');
    }
  });

  it('AC-F006-02: when the whole pool is cooling, thaw the word closest to eligible', () => {
    const a = makeWord('apple', 1);
    const b = makeWord('ant', 999); // high priority but thaws later — must not win
    const pool = [a, b];
    const states = new Map<string, WordState>([
      ['apple', { exposureCount: 1, nextEligibleAt: 4 }],
      ['ant', { exposureCount: 2, nextEligibleAt: 9 }],
    ]);
    const picked = pickWord(pool, states, 1, mulberry32(42));
    expect(picked?.word).toBe('apple');
  });

  it('AC-F006-03: higher-priority words are picked significantly more often', () => {
    const hi = makeWord('hi', 100);
    const lo = makeWord('lo', 1);
    const pool = [hi, lo];
    const states = new Map<string, WordState>();
    const random = mulberry32(7);
    const counts = { hi: 0, lo: 0 };
    const TRIALS = 10000;
    for (let i = 0; i < TRIALS; i++) {
      const w = pickWord(pool, states, i, random)!;
      counts[w.word as 'hi' | 'lo'] += 1;
    }
    // Expected ratio ~100:1; assert a very loose bound to avoid flakiness.
    expect(counts.hi).toBeGreaterThan(counts.lo * 20);
  });

  it('weighted random respects interval changes from word-list settings (AC-F006-04)', () => {
    // With intervals [1], a word exposed at count 1 is eligible again at 2.
    const s = recordExposure(initialState(), 1, [1]);
    expect(s.nextEligibleAt).toBe(2);
    expect(isEligible(s, 2)).toBe(true);
  });

  it('returns null only for an empty pool', () => {
    expect(pickWord([], new Map(), 0)).toBeNull();
  });
});
