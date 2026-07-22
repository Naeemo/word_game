import type { WordEntry, ParentConfig } from './types';

/**
 * Four-segment reading per PRD F-003:
 * word(EN) → word zh → sentence(EN) → sentence zh, sequential, no overlap.
 * Each segment plays a pre-generated recording (audio/{key}.<seg>.mp3);
 * a missing/undecodable file falls back to speechSynthesis for that segment.
 * onDone always fires so the game never blocks.
 */

const FALLBACK_UNLOCK_MS = 2000;

/** File-name key: lowercase, non [a-z0-9] → "_" (ice cream→ice_cream, o'clock→o_clock). */
export function wordKey(word: string): string {
  return word.toLowerCase().replace(/[^a-z0-9]/g, '_');
}

/**
 * Quality rank of a voice by name: macOS Premium/Enhanced/Siri voices are
 * neural and natural-sounding; compact bundled voices sound robotic.
 */
function voiceQuality(v: SpeechSynthesisVoice): number {
  const n = v.name.toLowerCase();
  if (n.includes('premium')) return 3;
  if (n.includes('enhanced')) return 2;
  if (n.includes('siri')) return 1;
  return 0;
}

/**
 * Pick the highest-quality (Premium > Enhanced > Siri) voice available for
 * the language, preferring exact-lang matches. Used only for TTS fallback.
 */
function pickVoice(lang: string): SpeechSynthesisVoice | null {
  try {
    const voices = speechSynthesis.getVoices();
    const prefix = lang.split('-')[0];
    const candidates = voices.filter((v) => v.lang === lang || v.lang.startsWith(prefix));
    if (candidates.length === 0) return null;
    candidates.sort((a, b) => {
      const exact = Number(b.lang === lang) - Number(a.lang === lang);
      return exact !== 0 ? exact : voiceQuality(b) - voiceQuality(a);
    });
    return candidates[0];
  } catch {
    return null;
  }
}

interface Segment {
  text: string;
  lang: string;
  /** Recording URL for this segment, e.g. audio/ice_cream.s_en.mp3. */
  audioUrl: string;
}

export function buildSegments(word: WordEntry, config: ParentConfig): Segment[] {
  const key = wordKey(word.word);
  const segments: Segment[] = [{ text: word.word, lang: 'en-US', audioUrl: `audio/${key}.en.mp3` }];
  if (config.readChinese && word.zh)
    segments.push({ text: word.zh, lang: 'zh-CN', audioUrl: `audio/${key}.zh.mp3` });
  if (word.sentenceEn)
    segments.push({ text: word.sentenceEn, lang: 'en-US', audioUrl: `audio/${key}.s_en.mp3` });
  if (config.readChinese && word.sentenceZh)
    segments.push({ text: word.sentenceZh, lang: 'zh-CN', audioUrl: `audio/${key}.s_zh.mp3` });
  return segments;
}

/** The Audio element currently playing (or null), so stopSpeaking can halt it. */
let currentAudio: HTMLAudioElement | null = null;

function stopCurrentAudio(): void {
  if (!currentAudio) return;
  const a = currentAudio;
  currentAudio = null;
  a.onended = null;
  a.onerror = null;
  try {
    a.pause();
  } catch {
    /* ignore */
  }
}

/**
 * Play the full sequence, then call onDone. Each segment first tries its
 * pre-generated recording; on missing file / decode failure it falls back to
 * speechSynthesis. Safe when speechSynthesis is missing entirely — audio still
 * plays, and a failed segment just advances. A per-segment watchdog keeps the
 * game from soft-locking when neither audio nor TTS reports completion.
 */
export function playSequence(word: WordEntry, config: ParentConfig, onDone: () => void): void {
  let finished = false;
  const finish = () => {
    if (!finished) {
      finished = true;
      stopCurrentAudio();
      onDone();
    }
  };

  const segments = buildSegments(word, config);
  if (segments.length === 0) {
    window.setTimeout(finish, FALLBACK_UNLOCK_MS);
    return;
  }

  try {
    if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
  } catch {
    /* ignore */
  }
  stopCurrentAudio();

  let index = 0;
  let watchdog: number | undefined;

  const speakNext = () => {
    if (finished) return;
    if (index >= segments.length) {
      finish();
      return;
    }
    const seg = segments[index++];
    let advanced = false;
    const advance = () => {
      if (advanced) return;
      advanced = true;
      window.clearTimeout(watchdog);
      stopCurrentAudio();
      speakNext();
    };
    // Desktop Chrome can stop mid-utterance without ever firing onend/onerror,
    // and a stalled Audio element may never fire onended; a per-segment
    // watchdog keeps the game from soft-locking on busyRef.
    watchdog = window.setTimeout(
      () => {
        try {
          if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
        } catch {
          /* ignore */
        }
        advance();
      },
      4000 + seg.text.length * 200,
    );

    const fallbackSpeak = () => {
      if (finished || advanced) return;
      if (typeof speechSynthesis === 'undefined') {
        advance();
        return;
      }
      const utterance = new SpeechSynthesisUtterance(seg.text);
      utterance.lang = seg.lang;
      utterance.rate = config.rate;
      const voice = pickVoice(seg.lang);
      if (voice) utterance.voice = voice;
      utterance.onend = advance;
      utterance.onerror = advance;
      try {
        speechSynthesis.speak(utterance);
      } catch {
        advance();
      }
    };

    const audio = new Audio(seg.audioUrl);
    currentAudio = audio;
    audio.playbackRate = config.rate;
    audio.onended = advance;
    audio.onerror = () => {
      if (currentAudio === audio) currentAudio = null;
      fallbackSpeak();
    };
    audio.play().catch(() => {
      if (currentAudio === audio) currentAudio = null;
      fallbackSpeak();
    });
  };

  speakNext();
}

export function stopSpeaking(): void {
  stopCurrentAudio();
  try {
    if (typeof speechSynthesis !== 'undefined') speechSynthesis.cancel();
  } catch {
    /* ignore */
  }
}
