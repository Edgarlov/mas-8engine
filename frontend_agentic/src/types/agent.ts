export type NodeScore = 'SURE' | 'MAYBE' | 'IMPOSSIBLE';

export interface ThoughtNode {
  id: string;
  parent_id: string | null;
  thought: string;
  score: NodeScore;
  evaluation: string;
  depth: number;
  payload?: Record<string, unknown>;
}

export interface AgentResponse {
  agent_id: string;
  status: string;
  data: Record<string, unknown>;
  cnf_proof?: string[] | null;
  score: NodeScore;
}

export interface SolveResponse {
  query: string;
  thought_tree: ThoughtNode[];
  delegation_trace: AgentResponse[];
  pruning_log: Array<{ node_id: string; reason: string; depth: number }>;
  optimal_solution: string | null;
  generative_ui_schema?: GenerativeUISchema | null;
  execution_time_ms: number;
}

// ── Generative UI JSON Schema Specification ──

export type UIComponentType =
  | 'metric_grid'
  | 'decision_badge'
  | 'probability_meter'
  | 'sat_proof_card'
  | 'callout_banner'
  | 'data_table'
  | 'code_block'
  | 'action_bar';

export interface MetricItem {
  label: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
}

export interface UIComponentSchema {
  id: string;
  type: UIComponentType;
  title?: string;
  props: Record<string, unknown>;
}

export interface GenerativeUISchema {
  layout: 'single' | 'grid' | 'stacked';
  components: UIComponentSchema[];
}
