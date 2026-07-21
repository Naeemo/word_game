import { useState } from 'react';
import { motion } from 'framer-motion';
import type { WordEntry } from '../types';

const EMOJI_PLACEHOLDER = '🖼️';

/**
 * Word card per F-002: image + uppercase word with highlighted first letter.
 * Falls back to an emoji placeholder if the image file is missing (F-002 AC-02).
 */
export function WordCard({ word }: { word: WordEntry }) {
  const [imgError, setImgError] = useState(false);
  const upper = word.word.toUpperCase();
  const highlightIndex =
    word.matchType === 'contains' ? upper.indexOf(word.letter.toUpperCase()) : 0;

  return (
    <motion.div
      key={word.word + word.letter}
      initial={{ scale: 0.5, opacity: 0, y: 40, rotate: -3 }}
      animate={{ scale: 1, opacity: 1, y: 0, rotate: 0 }}
      exit={{ scale: 0.7, opacity: 0, y: 30, transition: { duration: 0.18 } }}
      transition={{ type: 'spring', stiffness: 260, damping: 18 }}
      className="flex flex-col items-center gap-6 rounded-3xl bg-white/90 p-8 shadow-2xl"
    >
      <motion.div
        initial={{ scale: 0.7, rotate: -5 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 13, delay: 0.08 }}
        className="flex h-64 w-64 items-center justify-center overflow-hidden rounded-2xl bg-sky-50 sm:h-80 sm:w-80"
      >
        {imgError ? (
          <span className="text-8xl" role="img" aria-label="placeholder">
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
      <div className="text-6xl font-black tracking-widest text-slate-800 sm:text-7xl">
        {upper.split('').map((ch, i) => (
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
            {ch}
          </motion.span>
        ))}
      </div>
    </motion.div>
  );
}
