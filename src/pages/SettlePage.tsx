import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import type { WordEntry } from '../types';

const LONG_PRESS_MS = 3000;

const FLOATERS = [
  { emoji: '🎈', left: '8%', delay: 0, duration: 3.2 },
  { emoji: '🎉', left: '22%', delay: 0.5, duration: 3.8 },
  { emoji: '⭐', left: '45%', delay: 0.2, duration: 3.0 },
  { emoji: '🎈', left: '68%', delay: 0.8, duration: 4.0 },
  { emoji: '🌟', left: '85%', delay: 0.4, duration: 3.4 },
];

interface Props {
  roundWords: WordEntry[];
  totalScore: number;
  onExit: () => void;
}

/**
 * Settle page (F-010): celebration + round review + total score.
 * Locked by design: NO visible "continue" entry anywhere. Parents long-press
 * the invisible top-left corner for 3 seconds to return to the config page.
 */
export function SettlePage({ roundWords, totalScore, onExit }: Props) {
  const timerRef = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timerRef.current), []);

  const startPress = () => {
    window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(onExit, LONG_PRESS_MS);
  };
  const cancelPress = () => window.clearTimeout(timerRef.current);

  return (
    <div className="relative flex min-h-screen flex-col items-center overflow-hidden bg-gradient-to-b from-amber-100 to-sky-100 p-6">
      {/* Hidden parent gesture zone: invisible, top-left, long-press 3s */}
      <div
        className="absolute left-0 top-0 h-16 w-16"
        onPointerDown={startPress}
        onPointerUp={cancelPress}
        onPointerLeave={cancelPress}
        onContextMenu={(e) => e.preventDefault()}
      />

      {/* Gentle floating celebration emojis, behind the content */}
      {FLOATERS.map((f, i) => (
        <motion.div
          key={i}
          initial={{ y: '105vh', opacity: 0 }}
          animate={{ y: [null, '-8vh', '-14vh', '-8vh'], opacity: [0, 1, 1, 1] }}
          transition={{
            delay: f.delay,
            duration: f.duration,
            repeat: Infinity,
            repeatType: 'reverse',
            ease: 'easeInOut',
          }}
          className="pointer-events-none absolute text-4xl"
          style={{ left: f.left }}
        >
          {f.emoji}
        </motion.div>
      ))}

      <motion.div
        initial={{ scale: 0, rotate: -30 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 12 }}
        className="mt-8 text-7xl"
      >
        🎉
      </motion.div>
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        className="mt-4 text-4xl font-black text-amber-600"
      >
        今天玩得真棒！
      </motion.h1>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.5 }}
        className="mt-2 flex items-center gap-2 text-2xl font-bold text-slate-700"
      >
        <span>⭐</span>
        <span>{totalScore}</span>
      </motion.div>

      <div className="mt-8 grid w-full max-w-3xl grid-cols-3 gap-4 sm:grid-cols-4 md:grid-cols-5">
        {roundWords.map((w, i) => (
          <motion.div
            key={`${w.word}-${i}`}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: Math.min(0.6 + i * 0.05, 1.5), duration: 0.3 }}
            className="flex flex-col items-center gap-1 rounded-2xl bg-white/90 p-3 shadow"
          >
            <img src={w.image} alt={w.word} className="h-16 w-16 object-contain" />
            <span className="text-lg font-bold text-slate-700">{w.word.toUpperCase()}</span>
          </motion.div>
        ))}
      </div>

      <div className="mt-8 text-3xl">🌙 明天再来玩哦</div>
    </div>
  );
}
