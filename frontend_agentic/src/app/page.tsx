'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Cpu,
  Layers,
  Sparkles,
  Zap,
  Activity,
  Code2,
  Terminal,
  ShieldCheck,
  CheckCircle,
  LayoutGrid,
} from 'lucide-react';
import { AgentPromptInput } from '@/components/AgentPromptInput';
import { AgentThinkingCanvas } from '@/components/AgentThinkingCanvas';
import { GenerativeUIRenderer } from '@/components/GenerativeUIRenderer';
import { SolveResponse, GenerativeUISchema } from '@/types/agent';

export default function Home() {
  const [response, setResponse] = useState<SolveResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'generative_ui' | 'thinking_canvas' | 'json_schema'>('generative_ui');

  // Standby initial state for fast interactive response

  const handleSolve = async (query: string, maxDepth: number, branchingFactor: number) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/agent/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          max_depth: maxDepth,
          branching_factor: branchingFactor,
        }),
      });

      if (res.ok) {
        const data: SolveResponse = await res.json();
        setResponse(data);
      }
    } catch (err) {
      console.error('Error executing solve:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Dynamic UI Schema directly consumed from Backend API response
  const uiSchema: GenerativeUISchema = response?.generative_ui_schema || {
    layout: 'grid',
    components: response?.optimal_solution
      ? [
          {
            id: 'c1',
            type: 'callout_banner',
            props: {
              variant: 'success',
              message: response.optimal_solution,
            },
          },
        ]
      : [],
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 p-4 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* ── Top Glassmorphism Header ── */}
      <header className="glass-panel-glow p-6 rounded-3xl border border-blue-500/30 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-blue-600/10 via-purple-600/10 to-transparent rounded-full blur-3xl pointer-events-none"></div>

        <div>
          <div className="flex items-center gap-3">
            <span className="p-2.5 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg shadow-blue-500/20">
              <Cpu className="w-6 h-6 text-white" />
            </span>
            <div>
              <h1 className="text-xl md:text-2xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-blue-400">
                Arquitectura Frontend Generativa & Streaming UI Agéntica
              </h1>
              <p className="text-xs text-slate-400 font-medium mt-0.5 flex items-center gap-2">
                <span>Next.js 15 (App Router)</span> · <span>React Server Components</span> · <span>Vercel AI SDK</span> · <span>MAS-8ENGINE</span>
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-slate-900/80 px-4 py-2 rounded-xl border border-slate-800 text-xs">
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span> Backend Conectado
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300 font-mono">
            {response ? `${response.execution_time_ms.toFixed(1)} ms` : 'Standby'}
          </span>
        </div>
      </header>

      {/* ── Prompt Input Section ── */}
      <section>
        <AgentPromptInput onSolve={handleSolve} isLoading={isLoading} />
      </section>

      {/* ── Navigation Tabs ── */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab('generative_ui')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'generative_ui'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
              : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Sparkles className="w-4 h-4" /> Generative UI (Componentes Dinámicos)
        </button>

        <button
          onClick={() => setActiveTab('thinking_canvas')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'thinking_canvas'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
              : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Layers className="w-4 h-4" /> Canvas de Pensamiento (ToT / MCTS)
        </button>

        <button
          onClick={() => setActiveTab('json_schema')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'json_schema'
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
              : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <Code2 className="w-4 h-4" /> Esquema JSON Generado
        </button>
      </div>

      {/* ── Tab Content ── */}
      <main>
        {activeTab === 'generative_ui' && (
          <section className="space-y-6">
            <GenerativeUIRenderer schema={uiSchema} isStreaming={isLoading} />
          </section>
        )}

        {activeTab === 'thinking_canvas' && response && (
          <section>
            <AgentThinkingCanvas
              thoughtTree={response.thought_tree}
              delegationTrace={response.delegation_trace}
              pruningLog={response.pruning_log}
            />
          </section>
        )}

        {activeTab === 'json_schema' && (
          <section className="glass-panel p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-slate-300">
              <Terminal className="w-4 h-4 text-emerald-400" /> Esquema JSON UI Estructurado:
            </div>
            <pre className="bg-slate-950 p-4 rounded-xl border border-slate-850 font-mono text-xs text-slate-200 overflow-x-auto max-h-[500px]">
              <code>{JSON.stringify(uiSchema, null, 2)}</code>
            </pre>
          </section>
        )}
      </main>
    </div>
  );
}
