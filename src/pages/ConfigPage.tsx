import { useState } from 'react';
import type { ParentConfig } from '../types';

interface Props {
  config: ParentConfig;
  onSave: (config: ParentConfig) => void;
  onStart: () => void;
}

/**
 * Parent config page (F-009): round size, Chinese toggle, speech rate.
 */
export function ConfigPage({ config, onSave, onStart }: Props) {
  const [roundSize, setRoundSize] = useState(String(config.roundSize));
  const [readChinese, setReadChinese] = useState(config.readChinese);
  const [rate, setRate] = useState(config.rate);
  const [error, setError] = useState('');

  const handleSave = () => {
    const n = Number(roundSize);
    if (!Number.isInteger(n) || n < 1 || n > 500) {
      setError('每轮词数必须是 1–500 之间的整数');
      return;
    }
    setError('');
    onSave({ roundSize: n, readChinese, rate });
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-sky-100 p-6">
      <div className="w-full max-w-md rounded-3xl bg-white p-8 shadow-xl">
        <h1 className="mb-6 text-center text-3xl font-bold text-slate-800">家长设置</h1>

        <label className="mb-4 block">
          <span className="mb-1 block text-lg text-slate-600">每轮词数</span>
          <input
            type="number"
            min={1}
            max={500}
            value={roundSize}
            onChange={(e) => setRoundSize(e.target.value)}
            className="w-full rounded-xl border-2 border-slate-200 px-4 py-2 text-xl focus:border-sky-400 focus:outline-none"
          />
        </label>

        <label className="mb-4 flex items-center gap-3">
          <input
            type="checkbox"
            checked={readChinese}
            onChange={(e) => setReadChinese(e.target.checked)}
            className="h-6 w-6 accent-sky-500"
          />
          <span className="text-lg text-slate-600">朗读中文</span>
        </label>

        <div className="mb-6">
          <span className="mb-1 block text-lg text-slate-600">语速</span>
          <div className="flex gap-3">
            {[
              { label: '慢', value: 0.6 },
              { label: '正常', value: 0.9 },
            ].map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setRate(opt.value)}
                className={`flex-1 rounded-xl border-2 px-4 py-2 text-lg ${
                  rate === opt.value
                    ? 'border-sky-500 bg-sky-50 font-bold text-sky-700'
                    : 'border-slate-200 text-slate-500'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="mb-4 text-center text-red-500">{error}</p>}

        <div className="flex gap-3">
          <button
            type="button"
            onClick={handleSave}
            className="flex-1 rounded-xl bg-slate-200 px-4 py-3 text-xl font-bold text-slate-700 hover:bg-slate-300"
          >
            保存
          </button>
          <button
            type="button"
            onClick={() => {
              handleSave();
              const n = Number(roundSize);
              if (Number.isInteger(n) && n >= 1 && n <= 500) onStart();
            }}
            className="flex-1 rounded-xl bg-sky-500 px-4 py-3 text-xl font-bold text-white hover:bg-sky-600"
          >
            开始游戏 ▶
          </button>
        </div>
      </div>
    </div>
  );
}
