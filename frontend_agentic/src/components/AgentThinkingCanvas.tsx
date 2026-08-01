'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch,
  CheckCircle,
  HelpCircle,
  XCircle,
  Eye,
  Cpu,
  Layers,
  Sparkles,
} from 'lucide-react';
import { ThoughtNode, AgentResponse, NodeScore } from '@/types/agent';

interface Props {
  thoughtTree: ThoughtNode[];
  delegationTrace: AgentResponse[];
  pruningLog: Array<{ node_id: string; reason: string; depth: number }>;
  onSelectNode?: (node: ThoughtNode) => void;
}

export function AgentThinkingCanvas({
  thoughtTree,
  delegationTrace,
  pruningLog,
  onSelectNode,
}: Props) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    thoughtTree.length > 0 ? thoughtTree[0].id : null
  );

  const selectedNode = thoughtTree.find((n) => n.id === selectedNodeId) || thoughtTree[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* ── Visual ToT Graph Column ── */}
      <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-sm text-slate-100">
              Árbol de Pensamiento Agéntico (ToT / MCTS Canvas)
            </h3>
          </div>
          <div className="flex items-center gap-3 text-xs font-medium">
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span> SURE
            </span>
            <span className="flex items-center gap-1 text-amber-400">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span> MAYBE
            </span>
            <span className="flex items-center gap-1 text-rose-400">
              <span className="w-2 h-2 rounded-full bg-rose-400"></span> IMPOSSIBLE (Podado)
            </span>
          </div>
        </div>

        {/* ── Tree View Nodes ── */}
        <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
          {thoughtTree.map((node, idx) => {
            const isSelected = node.id === selectedNodeId;
            const isPruned = pruningLog.some((p) => p.node_id === node.id);

            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => {
                  setSelectedNodeId(node.id);
                  if (onSelectNode) onSelectNode(node);
                }}
                className={`p-4 rounded-xl border transition-all cursor-pointer relative ${
                  isSelected
                    ? 'glass-panel-glow border-blue-500/60 bg-blue-950/20'
                    : isPruned
                    ? 'border-rose-900/40 bg-rose-950/10 opacity-60'
                    : 'border-slate-800/80 bg-slate-900/40 hover:border-slate-700'
                }`}
                style={{ marginLeft: `${node.depth * 20}px` }}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-2.5">
                    <ScoreIcon score={node.score} isPruned={isPruned} />
                    <div>
                      <div className="text-xs font-semibold text-slate-300 flex items-center gap-2">
                        <span>Nodo {node.id.substring(0, 6)}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                          Depth {node.depth}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 mt-1 font-medium leading-relaxed line-clamp-2">
                        {node.thought}
                      </p>
                    </div>
                  </div>
                  <Eye className={`w-4 h-4 shrink-0 ${isSelected ? 'text-blue-400' : 'text-slate-600'}`} />
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* ── Node Telemetry & Subordinate Agent Response Column ── */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
            <Cpu className="w-5 h-5 text-purple-400" />
            <h3 className="font-semibold text-sm text-slate-100">
              Telemetría del Nodo Seleccionado
            </h3>
          </div>

          <AnimatePresence mode="wait">
            {selectedNode ? (
              <motion.div
                key={selectedNode.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-4"
              >
                <div>
                  <div className="text-[11px] text-slate-400 uppercase font-semibold tracking-wider">
                    Hipótesis Analizada:
                  </div>
                  <p className="text-xs text-slate-200 font-medium mt-1 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-850">
                    {selectedNode.thought}
                  </p>
                </div>

                <div>
                  <div className="text-[11px] text-slate-400 uppercase font-semibold tracking-wider mb-2">
                    Consenso del Comité de Agentes:
                  </div>
                  <div className="space-y-2">
                    <AgentBadge
                      name="Agente 1 (Perceptivo - Bayes/Fuzzy)"
                      status="SUCCESS"
                      metric="P(H|E) = 89.1%"
                    />
                    <AgentBadge
                      name="Agente 2 (Memoria - CBR/AGM)"
                      status="SUCCESS"
                      metric="Coincidencia CBR 88.5%"
                    />
                    <AgentBadge
                      name="Agente 3 (Verificador - Z3/Nash)"
                      status="SUCCESS"
                      metric="Demostración Z3 SAT"
                    />
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="text-xs text-slate-500 py-8 text-center">
                Selecciona un nodo para inspeccionar sus datos.
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

function ScoreIcon({ score, isPruned }: { score: NodeScore; isPruned: boolean }) {
  if (isPruned) {
    return <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />;
  }
  switch (score) {
    case 'SURE':
      return <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />;
    case 'MAYBE':
      return <HelpCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />;
    case 'IMPOSSIBLE':
      return <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />;
  }
}

function AgentBadge({
  name,
  status,
  metric,
}: {
  name: string;
  status: string;
  metric: string;
}) {
  return (
    <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between text-xs">
      <span className="text-slate-300 font-medium text-[11px]">{name}</span>
      <span className="text-purple-400 font-semibold text-[10px] bg-purple-950/60 px-2 py-0.5 rounded border border-purple-500/30">
        {metric}
      </span>
    </div>
  );
}
