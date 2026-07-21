import { useEffect, useState } from 'react';
import type { ParentConfig, WordEntry, WordList } from './types';
import { loadWordList } from './wordlist';
import { loadConfig, loadScore, saveConfig } from './storage';
import { ConfigPage } from './pages/ConfigPage';
import { GamePage } from './pages/GamePage';
import { SettlePage } from './pages/SettlePage';

type Screen = 'config' | 'game' | 'settle';

export default function App() {
  const [wordList, setWordList] = useState<WordList | null>(null);
  const [loadError, setLoadError] = useState('');
  const [screen, setScreen] = useState<Screen>('config');
  const [config, setConfig] = useState<ParentConfig>(() => loadConfig());
  const [roundWords, setRoundWords] = useState<WordEntry[]>([]);
  const [gameKey, setGameKey] = useState(0);

  useEffect(() => {
    loadWordList()
      .then(setWordList)
      .catch((e: unknown) => setLoadError(e instanceof Error ? e.message : String(e)));
  }, []);

  // F-007 AC-02: clear error instead of a white screen.
  if (loadError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-red-50 p-8">
        <div className="max-w-lg rounded-2xl bg-white p-8 text-center shadow-xl">
          <div className="mb-4 text-5xl">⚠️</div>
          <h1 className="mb-2 text-2xl font-bold text-red-600">词表加载失败</h1>
          <p className="text-slate-600">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!wordList) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-sky-100 text-2xl text-slate-500">
        加载中…
      </div>
    );
  }

  const handleSaveConfig = (next: ParentConfig) => {
    setConfig(next);
    saveConfig(next);
  };

  if (screen === 'settle') {
    return (
      <SettlePage
        roundWords={roundWords}
        totalScore={loadScore()}
        onExit={() => {
          setScreen('config');
        }}
      />
    );
  }

  if (screen === 'game') {
    return (
      <GamePage
        key={gameKey}
        words={wordList.words}
        intervals={wordList.settings.intervals}
        config={config}
        onRoundComplete={(played) => {
          setRoundWords(played);
          setScreen('settle');
        }}
      />
    );
  }

  return (
    <ConfigPage
      config={config}
      onSave={handleSaveConfig}
      onStart={() => {
        setGameKey((k) => k + 1);
        setScreen('game');
      }}
    />
  );
}
