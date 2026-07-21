import type { WordEntry, ParentConfig } from './types';

/**
 * Four-segment reading per PRD F-003:
 * word(EN) → word zh → sentence(EN) → sentence zh, sequential, no overlap.
 * Missing/unsupported TTS never blocks the flow: onDone always fires.
 */

const FALLBACK_UNLOCK_MS = 2000;

function pickVoice(lang: string): SpeechSynthesisVoice | null {
  try {
    const voices = speechSynthesis.getVoices();
    return (
      voices.find((v) => v.lang === lang) ??
      voices.find((v) => v.lang.startsWith(lang.split('-')[0])) ??
      null
    );
  } catch {
    return null;
  }
}

interface Segment {
  text: string;
  lang: string;
}

export function buildSegments(word: WordEntry, config: ParentConfig): Segment[] {
  const segments: Segment[] = [{ text: word.word, lang: 'en-US' }];
  if (config.readChinese && word.zh) segments.push({ text: word.zh, lang: 'zh-CN' });
  if (word.sentenceEn) segments.push({ text: word.sentenceEn, lang: 'en-US' });
  if (config.readChinese && word.sentenceZh) segments.push({ text: word.sentenceZh, lang: 'zh-CN' });
  return segments;
}

/**
 * Play the full sequence, then call onDone. Safe when speechSynthesis is
 * missing or has no voices — in that case onDone fires after a short delay
 * so the card still shows and the game is not blocked.
 */
export function playSequence(word: WordEntry, config: ParentConfig, onDone: () => void): void {
  let finished = false;
  const finish = () => {
    if (!finished) {
      finished = true;
      onDone();
    }
  };

  if (typeof speechSynthesis === 'undefined') {
    window.setTimeout(finish, FALLBACK_UNLOCK_MS);
    return;
  }

  const segments = buildSegments(word, config);
  if (segments.length === 0) {
    window.setTimeout(finish, FALLBACK_UNLOCK_MS);
    return;
  }

  try {
    speechSynthesis.cancel();
  } catch {
    window.setTimeout(finish, FALLBACK_UNLOCK_MS);
    return;
  }

  let index = 0;
  let watchdog: number | undefined;
  const speakNext = () => {
    if (finished) return;
    if (index >= segments.length) {
      finish();
      return;
    }
    const seg = segments[index++];
    const utterance = new SpeechSynthesisUtterance(seg.text);
    utterance.lang = seg.lang;
    utterance.rate = config.rate;
    const voice = pickVoice(seg.lang);
    if (voice) utterance.voice = voice;
    // Desktop Chrome can stop mid-utterance without ever firing onend/onerror;
    // a per-segment watchdog keeps the game from soft-locking on busyRef.
    let advanced = false;
    const advance = () => {
      if (advanced) return;
      advanced = true;
      window.clearTimeout(watchdog);
      speakNext();
    };
    utterance.onend = advance;
    utterance.onerror = advance;
    watchdog = window.setTimeout(
      () => {
        try {
          speechSynthesis.cancel(); // unstick the hung utterance
        } catch {
          /* ignore */
        }
        advance();
      },
      4000 + seg.text.length * 200,
    );
    try {
      speechSynthesis.speak(utterance);
    } catch {
      advance();
    }
  };

  speakNext();
}

export function stopSpeaking(): void {
  try {
    if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
  } catch {
    /* ignore */
  }
}
