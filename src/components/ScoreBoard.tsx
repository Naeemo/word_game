import { AnimatePresence, motion } from 'framer-motion';

/**
 * Score display with a "+1" floating animation (F-011 AC-02).
 */
export function ScoreBoard({ score, tick }: { score: number; tick: number }) {
  return (
    <div className="relative flex items-center gap-2 rounded-full bg-amber-300 px-5 py-2 shadow">
      <motion.span
        key={`star-${tick}`}
        animate={tick > 0 ? { rotate: [0, -18, 14, 0], scale: [1, 1.3, 1] } : undefined}
        transition={{ duration: 0.45 }}
        className="inline-block text-2xl"
      >
        ⭐
      </motion.span>
      <motion.span
        key={`score-${score}`}
        initial={{ scale: 1.6 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 420, damping: 14 }}
        className="inline-block text-2xl font-bold text-amber-900"
      >
        {score}
      </motion.span>
      <AnimatePresence>
        {tick > 0 && (
          <motion.span
            key={tick}
            initial={{ opacity: 1, y: 0, scale: 0.6 }}
            animate={{ opacity: 0, y: -52, scale: 1.25 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="absolute -right-2 -top-2 text-2xl font-black text-orange-500"
          >
            +1
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
}
