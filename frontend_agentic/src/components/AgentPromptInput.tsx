'use client';

import React, { useState } from 'react';
import { Send, Sparkles, Sliders, RefreshCw, Terminal } from 'lucide-react';

interface Props {
  onSolve: (query: string, maxDepth: number, branchingFactor: number) => void;
  isLoading: boolean;
}

export function AgentPromptInput({ onSolve, isLoading }: Props) {
  const [query, setQuery] = useState(
    'ejecuta un analisis como una consultora de alto estanding sobre las tendencias de diseño de frontend de sistemas agenticos de compañias pioneras y crea un stack tecnologico y de estilos de ultima generacion'
  );
  const [maxDepth, setMaxDepth] = useState(1);
  const [branchingFactor, setBranchingFactor] = useState(2);
  const [showConfig, setShowConfig] = useState(false);

  const presets = [
    {
      label: '🎨 Frontend Agéntico & Stack UI',
      query:
        'ejecuta un analisis como una consultora de alto estanding sobre las tendencias de diseño de frontend de sistemas agenticos de compañias pioneras y crea un stack tecnologico y de estilos de ultima generacion',
    },
    {
      label: '📈 Expansión & Cobertura Inflacionaria',
      query:
        'Evaluar la estrategia de expansión de mercado para una empresa de tecnología en América Latina considerando riesgos de inflación',
    },
    {
      label: '⚙️ Resiliencia de Infraestructura',
      query:
        'Optimizar la asignación de recursos en una infraestructura distribuida bajo condiciones de alta latencia y fallos aleatorios',
    },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSolve(query, maxDepth, branchingFactor);
    }
  };

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
      {/* ── Presets Bar ── */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none text-xs">
        <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] shrink-0 mr-1 flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" /> Presets:
        </span>
        {presets.map((preset, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setQuery(preset.query)}
            className="px-3 py-1.5 rounded-lg bg-slate-900/80 hover:bg-blue-950/40 border border-slate-800 hover:border-blue-500/40 text-slate-300 hover:text-blue-300 transition-all shrink-0 text-xs font-medium"
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* ── Prompt Input Form ── */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative rounded-xl overflow-hidden border border-slate-700/80 focus-within:border-blue-500/80 transition-all bg-slate-950/90 shadow-inner">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={3}
            placeholder="Escribe una consulta sistémica compleja para el comité de 8 motores agénticos..."
            className="w-full bg-transparent p-4 text-xs text-slate-100 placeholder-slate-500 focus:outline-none resize-none leading-relaxed font-sans"
          />

          <div className="flex justify-between items-center px-4 py-2 bg-slate-900/60 border-t border-slate-850">
            <button
              type="button"
              onClick={() => setShowConfig(!showConfig)}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 font-medium transition-colors"
            >
              <Sliders className="w-3.5 h-3.5 text-purple-400" />
              <span>Parámetros ToT (Depth: {maxDepth}, Branch: {branchingFactor})</span>
            </button>

            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-5 py-2 rounded-lg bg-gradient-to-r from-blue-600 via-purple-600 to-emerald-600 text-white text-xs font-semibold hover:opacity-90 transition-all flex items-center gap-2 shadow-lg shadow-blue-500/20 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Procesando...</span>
                </>
              ) : (
                <>
                  <span>Ejecutar Análisis</span>
                  <Send className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* ── Config Panel Dropdown ── */}
        {showConfig && (
          <div className="mt-3 p-4 rounded-xl glass-panel border border-slate-800 grid grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-300 font-semibold block mb-1">
                Profundidad Máxima MCTS (max_depth): {maxDepth}
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={maxDepth}
                onChange={(e) => setMaxDepth(Number(e.target.value))}
                className="w-full accent-blue-500"
              />
            </div>
            <div>
              <label className="text-slate-300 font-semibold block mb-1">
                Factor de Ramificación (branching_factor): {branchingFactor}
              </label>
              <input
                type="range"
                min="2"
                max="5"
                value={branchingFactor}
                onChange={(e) => setBranchingFactor(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
