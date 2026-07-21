import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import type { ParentConfig, WordEntry, WordState } from '../types';
import { initialState, pickWord, recordExposure } from '../scheduler';
import {
  loadExposure,
  loadGlobalCount,
  loadScore,
  saveExposure,
  saveGlobalCount,
  saveScore,
} from '../storage';
import { playSequence } from '../tts';
import { WordCard } from '../components/WordCard';
import { ScoreBoard } from '../components/ScoreBoard';

const LETTERS = 'abcdefghijklmnopqrstuvwxyz'.split('');

interface Props {
  words: WordEntry[];
  intervals: number[];
  config: ParentConfig;
  onRoundComplete: (roundWords: WordEntry[]) => void;
}

/**
 * Game screen (F-001/F-004/F-005/F-006): press a letter → scheduled word card +
 * four-segment reading + score +1. All keys are ignored while a word sequence
 * is playing (debounce), so long-press repeats never accumulate.
 */
export function GamePage({ words, intervals, config, onRoundComplete }: Props) {
  const [current, setCurrent] = useState<WordEntry | null>(null);
  const [notice, setNotice] = useState('');
  const [score, setScore] = useState(() => loadScore());
  const [scoreTick, setScoreTick] = useState(0);
  // Increments on every pick so the card re-animates even when the same word
  // is thawed twice in a row (key must change for framer-motion to remount).
  const [pickSeq, setPickSeq] = useState(0);

  const poolsRef = useRef<Map<string, WordEntry[]> | null>(null);
  if (!poolsRef.current) {
    const pools = new Map<string, WordEntry[]>();
    for (const w of words) {
      const pool = pools.get(w.letter);
      if (pool) pool.push(w);
      else pools.set(w.letter, [w]);
    }
    poolsRef.current = pools;
  }

  const busyRef = useRef(false);
  const statesRef = useRef<Map<string, WordState>>(loadExposure());
  // Persisted global pick counter (PRD §4.4): cooldowns keep their meaning
  // across sessions and new-round remounts.
  const globalCountRef = useRef(loadGlobalCount());
  const roundWordsRef = useRef<WordEntry[]>([]);
  const noticeTimerRef = useRef<number | undefined>(undefined);

  const handleLetter = useCallback(
    (letter: string) => {
      if (busyRef.current) return; // F-004: ignore everything mid-sequence

      const pool = poolsRef.current!.get(letter);
      if (!pool || pool.length === 0) {
        // F-001 AC-03: friendly notice, no score, no crash.
        setNotice('还没有这个词哦');
        window.clearTimeout(noticeTimerRef.current);
        noticeTimerRef.current = window.setTimeout(() => setNotice(''), 1500);
        return;
      }

      const word = pickWord(pool, statesRef.current, globalCountRef.current);
      if (!word) return;

      busyRef.current = true;
      globalCountRef.current += 1;
      saveGlobalCount(globalCountRef.current);

      // F-006: record exposure + cooldown; F-005: score +1; both persisted immediately.
      const prev = statesRef.current.get(word.word) ?? initialState();
      statesRef.current.set(
        word.word,
        recordExposure(prev, globalCountRef.current, intervals),
      );
      saveExposure(statesRef.current);

      setScore((s) => {
        const next = s + 1;
        saveScore(next);
        return next;
      });
      setScoreTick((t) => t + 1);

      roundWordsRef.current = [...roundWordsRef.current, word];
      setNotice('');
      setCurrent(word);
      setPickSeq((n) => n + 1);

      playSequence(word, config, () => {
        busyRef.current = false;
        if (roundWordsRef.current.length >= config.roundSize) {
          onRoundComplete(roundWordsRef.current);
        }
      });
    },
    [config, intervals, onRoundComplete],
  );

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.repeat) return; // long-press repeats never accumulate (F-004 AC-03)
      if (!/^[a-zA-Z]$/.test(e.key)) return; // non-letter keys: no response (F-001 AC-02)
      handleLetter(e.key.toLowerCase());
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [handleLetter]);

  return (
    <div className="flex min-h-screen flex-col bg-sky-100">
      <div className="flex items-center justify-between p-4">
        <ScoreBoard score={score} tick={scoreTick} />
        <div className="text-lg font-bold text-sky-700">
          {roundWordsRef.current.length}/{config.roundSize}
        </div>
      </div>

      <div className="flex flex-1 flex-col items-center justify-center gap-8 p-6">
        <AnimatePresence>
          {notice && (
            <motion.div
              initial={{ opacity: 0, scale: 0.7, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ type: 'spring', stiffness: 320, damping: 18 }}
              className="rounded-2xl bg-white/90 px-8 py-6 text-3xl font-bold text-slate-600 shadow"
            >
              {notice}
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence mode="wait">
          {current ? (
            <WordCard key={`${current.word}-${pickSeq}`} word={current} />
          ) : (
            !notice && (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-6"
              >
                <div className="grid max-w-2xl grid-cols-7 gap-2 sm:gap-3">
                  {LETTERS.map((l, i) => (
                    <motion.div
                      key={l}
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1, y: [0, -4, 0] }}
                      transition={{
                        opacity: { delay: i * 0.03, duration: 0.25 },
                        scale: { delay: i * 0.03, type: 'spring', stiffness: 300, damping: 14 },
                        y: {
                          delay: 0.8 + i * 0.06,
                          duration: 2.2,
                          repeat: Infinity,
                          ease: 'easeInOut',
                        },
                      }}
                      className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-2xl font-black text-sky-600 shadow sm:h-16 sm:w-16 sm:text-3xl"
                    >
                      {l.toUpperCase()}
                    </motion.div>
                  ))}
                </div>
                <div className="text-5xl">⌨️</div>
              </motion.div>
            )
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
