'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Zap,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Sparkles,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { GenerativeUISchema, UIComponentSchema, MetricItem } from '@/types/agent';

interface Props {
  schema: GenerativeUISchema;
  isStreaming?: boolean;
}

export function GenerativeUIRenderer({ schema, isStreaming = false }: Props) {
  if (!schema || !schema.components || schema.components.length === 0) {
    return null;
  }

  return (
    <div className="space-y-6">
      {schema.components.map((comp, idx) => (
        <motion.div
          key={comp.id || `comp-${idx}`}
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: idx * 0.1 }}
        >
          {renderComponent(comp, isStreaming)}
        </motion.div>
      ))}
    </div>
  );
}

function renderComponent(comp: UIComponentSchema, isStreaming: boolean) {
  switch (comp.type) {
    case 'metric_grid': {
      const items = (comp.props.items as MetricItem[]) || [];
      return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {items.map((item, i) => (
            <div
              key={i}
              className="glass-panel p-5 rounded-xl border border-slate-800/80 hover:border-blue-500/40 transition-all duration-300 group"
            >
              <div className="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
                <span>{item.label}</span>
                {item.trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                ) : item.trend === 'down' ? (
                  <TrendingDown className="w-4 h-4 text-rose-400" />
                ) : (
                  <Activity className="w-4 h-4 text-blue-400" />
                )}
              </div>
              <div className="text-2xl font-bold text-slate-100 group-hover:text-blue-400 transition-colors">
                {item.value}
              </div>
              {item.change && (
                <div className="mt-2 text-xs font-medium text-emerald-400 flex items-center gap-1">
                  <span>{item.change}</span>
                  {item.description && (
                    <span className="text-slate-500">· {item.description}</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }

    case 'probability_meter': {
      const title = (comp.props.title as string) || 'Probabilidad Posterior Bayesiana';
      const percentage = (comp.props.percentage as number) || 0;
      const subtitle = (comp.props.subtitle as string) || '';

      return (
        <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
          <div className="flex justify-between items-center text-sm font-semibold text-slate-200">
            <span className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-400" /> {title}
            </span>
            <span className="text-purple-400 font-bold">{percentage.toFixed(1)}%</span>
          </div>
          <div className="w-full h-3 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-800">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-400 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
          {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
        </div>
      );
    }

    case 'sat_proof_card': {
      const isSat = comp.props.satisfiable as boolean;
      const proofTrace = (comp.props.proofTrace as string[]) || [];

      return (
        <div
          className={`glass-panel p-5 rounded-xl border ${
            isSat
              ? 'border-emerald-500/30 bg-emerald-950/10'
              : 'border-rose-500/30 bg-rose-950/10'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {isSat ? (
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-rose-400" />
              )}
              <span className="font-semibold text-sm text-slate-100">
                Demostración Lógica Formal Z3 (SAT/CDCL)
              </span>
            </div>
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-bold uppercase tracking-wider ${
                isSat
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
              }`}
            >
              {isSat ? 'SATISFACIBLE (0 Contradicciones)' : 'INSATISFACIBLE (UNSAT)'}
            </span>
          </div>
          {proofTrace.length > 0 && (
            <div className="mt-3 bg-slate-950/80 p-3 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 space-y-1">
              <div className="text-slate-500 text-[10px] uppercase font-bold mb-1">
                Asignación de Modelo / Núcleo de Conflicto:
              </div>
              {proofTrace.map((clause, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-purple-400">├─</span>
                  <span>{clause}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    case 'callout_banner': {
      const message = (comp.props.message as string) || '';
      const variant = (comp.props.variant as 'info' | 'success' | 'warning') || 'info';

      return (
        <div
          className={`p-4 rounded-xl border flex items-start gap-3 ${
            variant === 'success'
              ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
              : variant === 'warning'
              ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
              : 'bg-blue-950/20 border-blue-500/30 text-blue-200'
          }`}
        >
          <Sparkles className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="text-sm leading-relaxed font-medium">{message}</div>
        </div>
      );
    }

    case 'code_block': {
      const code = (comp.props.code as string) || '';
      const language = (comp.props.language as string) || 'typescript';

      return (
        <div className="glass-panel rounded-xl overflow-hidden border border-slate-800">
          <div className="bg-slate-900/90 px-4 py-2 flex justify-between items-center border-b border-slate-800 text-xs text-slate-400 font-mono">
            <span className="flex items-center gap-1.5">
              <Code2 className="w-3.5 h-3.5 text-blue-400" /> {language}
            </span>
            <span>RSC Dynamic Chunk</span>
          </div>
          <pre className="p-4 bg-slate-950 text-xs font-mono text-slate-200 overflow-x-auto leading-relaxed">
            <code>{code}</code>
          </pre>
        </div>
      );
    }

    default:
      return null;
  }
}
