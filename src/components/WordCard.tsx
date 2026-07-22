import { useState } from 'react';
import { motion } from 'framer-motion';
import type { WordEntry } from '../types';

const EMOJI_PLACEHOLDER = '🖼️';

/**
 * Word card per F-002: large horizontal card (~60% of the screen) —
 * image on the left, lowercase word + Chinese meaning + EN/ZH example
 * sentence on the right. Falls back to an emoji placeholder if the image
 * file is missing (F-002 AC-02).
 */
export function WordCard({ word }: { word: WordEntry }) {
  const [imgError, setImgError] = useState(false);
  const display = word.word.toLowerCase();
  const highlightIndex =
    word.matchType === 'contains' ? display.indexOf(word.letter.toLowerCase()) : 0;

  return (
    <motion.div
      key={word.word + word.letter}
      initial={{ scale: 0.5, opacity: 0, y: 40, rotate: -3 }}
      animate={{ scale: 1, opacity: 1, y: 0, rotate: 0 }}
      exit={{ scale: 0.7, opacity: 0, y: 30, transition: { duration: 0.18 } }}
      transition={{ type: 'spring', stiffness: 260, damping: 18 }}
      className="flex h-[72vh] w-[85vw] max-w-6xl items-center gap-10 rounded-3xl bg-white/90 p-10 shadow-2xl"
    >
      <motion.div
        initial={{ scale: 0.7, rotate: -5 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 13, delay: 0.08 }}
        className="flex h-full flex-1 items-center justify-center overflow-hidden rounded-2xl bg-sky-50"
      >
        {imgError ? (
          <span className="text-9xl" role="img" aria-label="placeholder">
            {EMOJI_PLACEHOLDER}
          </span>
        ) : (
          <img
            src={word.image}
            alt={word.word}
            onError={() => setImgError(true)}
            className="h-full w-full object-contain"
          />
        )}
      </motion.div>

      <div className="flex flex-1 flex-col items-center gap-6">
        <div className="text-6xl font-black tracking-wider text-slate-800">
          {display.split('').map((ch, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, y: 16, scale: 0.5 }}
              animate={
                i === highlightIndex
                  ? { opacity: 1, y: 0, scale: [0.5, 1.35, 1] }
                  : { opacity: 1, y: 0, scale: 1 }
              }
              transition={{
                delay: 0.15 + 0.05 * i,
                type: 'spring',
                stiffness: 380,
                damping: 15,
              }}
              className={`inline-block ${i === highlightIndex ? 'text-orange-500' : ''}`}
            >
              {ch === ' ' ? ' ' : ch}
            </motion.span>
          ))}
        </div>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45, duration: 0.25 }}
          className="text-6xl font-bold text-sky-700"
        >
          {word.zh}
        </motion.div>
        {(word.sentenceEn || word.sentenceZh) && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.25 }}
            className="flex max-w-lg flex-col items-center gap-2 text-center"
          >
            {word.sentenceEn && (
              <div className="text-2xl font-semibold text-slate-600">{word.sentenceEn}</div>
            )}
            {word.sentenceZh && (
              <div className="text-2xl text-slate-400">{word.sentenceZh}</div>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
