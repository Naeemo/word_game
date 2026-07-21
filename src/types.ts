export interface WordEntry {
  word: string;
  letter: string;
  matchType: 'initial' | 'contains';
  priority: number;
  zh: string;
  sentenceEn?: string;
  sentenceZh?: string;
  image: string;
}

export interface WordList {
  settings: {
    intervals: number[];
  };
  words: WordEntry[];
}

/** Per-word exposure state, persisted in localStorage. */
export interface WordState {
  exposureCount: number;
  /**
   * Global pick index at/after which the word is eligible again.
   * Unused while exposureCount === 0 (never-exposed words are always eligible).
   */
  nextEligibleAt: number;
}

export interface ParentConfig {
  /** Words per round before the settle page appears. */
  roundSize: number;
  /** Read Chinese segments (word zh + sentence zh). */
  readChinese: boolean;
  /** Speech rate: 0.6 slow / 0.9 normal. */
  rate: number;
}

export const DEFAULT_CONFIG: ParentConfig = {
  roundSize: 20,
  readChinese: true,
  rate: 0.9,
};
