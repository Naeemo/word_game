import type { WordEntry, WordList } from './types';

/**
 * Load and validate the word list (PRD F-007).
 * Throws an Error with a clear message (including location) on bad data.
 */
export async function loadWordList(url = '/data/words.json'): Promise<WordList> {
  let raw: string;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    raw = await res.text();
  } catch (e) {
    throw new Error(`词表文件加载失败（${url}）：${e instanceof Error ? e.message : String(e)}`);
  }

  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch (e) {
    throw new Error(`词表 JSON 语法错误：${e instanceof Error ? e.message : String(e)}`);
  }

  const list = data as Partial<WordList>;
  if (!list || typeof list !== 'object' || !Array.isArray(list.words)) {
    throw new Error('词表格式错误：缺少顶层 words 数组');
  }
  const intervals = list.settings?.intervals;
  if (!Array.isArray(intervals) || intervals.length === 0 || !intervals.every((n) => Number.isInteger(n) && n > 0)) {
    throw new Error('词表格式错误：settings.intervals 必须是非空正整数数组');
  }

  const words: WordEntry[] = [];
  list.words.forEach((w, i) => {
    const where = `第 ${i + 1} 个词条（${(w as WordEntry)?.word ?? '?'}）`;
    if (!w || typeof w.word !== 'string' || w.word.length === 0) {
      throw new Error(`词表格式错误：${where}缺少 word`);
    }
    if (typeof w.letter !== 'string' || !/^[a-z]$/.test(w.letter)) {
      throw new Error(`词表格式错误：${where}letter 必须是单个小写字母`);
    }
    if (typeof w.priority !== 'number' || !(w.priority > 0)) {
      throw new Error(`词表格式错误：${where}priority 必须是正数`);
    }
    if (typeof w.zh !== 'string' || w.zh.length === 0) {
      throw new Error(`词表格式错误：${where}缺少中文释义 zh`);
    }
    if (typeof w.image !== 'string' || w.image.length === 0) {
      throw new Error(`词表格式错误：${where}缺少 image`);
    }
    words.push({
      word: w.word,
      letter: w.letter,
      matchType: w.matchType === 'contains' ? 'contains' : 'initial',
      priority: w.priority,
      zh: w.zh,
      sentenceEn: typeof w.sentenceEn === 'string' ? w.sentenceEn : undefined,
      sentenceZh: typeof w.sentenceZh === 'string' ? w.sentenceZh : undefined,
      image: w.image,
    });
  });

  return { settings: { intervals: [...intervals] }, words };
}

/** Group words into per-letter pools keyed by a-z. */
export function buildPools(words: WordEntry[]): Map<string, WordEntry[]> {
  const pools = new Map<string, WordEntry[]>();
  for (const w of words) {
    const pool = pools.get(w.letter);
    if (pool) pool.push(w);
    else pools.set(w.letter, [w]);
  }
  return pools;
}
