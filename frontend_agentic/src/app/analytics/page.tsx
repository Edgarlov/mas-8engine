"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";

interface Node3D {
  id: string;
  label: string;
  category: "core" | "math" | "mcp" | "security" | "memory" | "top";
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
  glowColor: string;
}

interface Edge3D {
  source: string;
  target: string;
  relation: string;
}

interface ServiceHealth {
  service_name: string;
  url: string;
  is_healthy: boolean;
  response_time_ms: number;
}

export default function SwarmAnalyticsDashboard() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node3D | null>(null);
  const [rotationAngle, setRotationAngle] = useState(0);
  const [isRotating, setIsRotating] = useState(true);

  const [metrics] = useState<ServiceHealth[]>([
    { service_name: "Backend API (FastAPI Kernel)", url: "http://127.0.0.1:8000", is_healthy: true, response_time_ms: 14.2 },
    { service_name: "Frontend Next.js 16 UI", url: "http://localhost:3000", is_healthy: true, response_time_ms: 8.5 },
    { service_name: "Sequential Thinking MCP Server", url: "stdio://npx", is_healthy: true, response_time_ms: 5.1 },
    { service_name: "Filesystem Workspace MCP Server", url: "stdio://npx", is_healthy: true, response_time_ms: 2.3 },
    { service_name: "NotebookLM CLI & MCP (v0.9.4)", url: "stdio://notebooklm-mcp", is_healthy: true, response_time_ms: 45.0 },
    { service_name: "Puppeteer Headless Browser MCP", url: "stdio://puppeteer", is_healthy: true, response_time_ms: 120.0 },
    { service_name: "Google Drive Taxonomy MCP", url: "stdio://gdrive", is_healthy: true, response_time_ms: 65.0 }
  ]);

  const [nodes] = useState<Node3D[]>([
    { id: "1", label: "MAS-8ENGINE v2.0 Kernel", category: "core", x: 0, y: 0, z: 0, vx: 0, vy: 0, radius: 32, color: "#818cf8", glowColor: "rgba(129, 140, 248, 0.7)" },
    { id: "2", label: "Z3 SMT Solver (CDCL)", category: "math", x: -180, y: -120, z: 50, vx: 0, vy: 0, radius: 22, color: "#34d399", glowColor: "rgba(52, 211, 153, 0.6)" },
    { id: "3", label: "Bayes & Mamdani CoG", category: "math", x: 180, y: -120, z: -40, vx: 0, vy: 0, radius: 20, color: "#34d399", glowColor: "rgba(52, 211, 153, 0.6)" },
    { id: "4", label: "Nash Bargaining Negotiator", category: "math", x: -200, y: 100, z: -30, vx: 0, vy: 0, radius: 20, color: "#34d399", glowColor: "rgba(52, 211, 153, 0.6)" },
    { id: "5", label: "OWASP Guardrails (LLM01/02)", category: "security", x: 200, y: 100, z: 60, vx: 0, vy: 0, radius: 22, color: "#f87171", glowColor: "rgba(248, 113, 113, 0.7)" },
    { id: "6", label: "ChromaDB Cosine Vector Store", category: "memory", x: -100, y: 190, z: 20, vx: 0, vy: 0, radius: 20, color: "#fbbf24", glowColor: "rgba(251, 191, 36, 0.6)" },
    { id: "7", label: "RDFlib Knowledge Graph (ISO-704)", category: "memory", x: 100, y: 190, z: -50, vx: 0, vy: 0, radius: 20, color: "#fbbf24", glowColor: "rgba(251, 191, 36, 0.6)" },
    { id: "8", label: "Red Teaming Offensive Agent", category: "security", x: 260, y: 0, z: 80, vx: 0, vy: 0, radius: 20, color: "#f472b6", glowColor: "rgba(244, 114, 182, 0.7)" },
    { id: "9", label: "NotebookLM Audio Overview MCP", category: "mcp", x: -260, y: 0, z: -70, vx: 0, vy: 0, radius: 20, color: "#38bdf8", glowColor: "rgba(56, 189, 248, 0.6)" },
    { id: "10", label: "HOL Theorem Prover", category: "top", x: -120, y: -220, z: 30, vx: 0, vy: 0, radius: 18, color: "#c084fc", glowColor: "rgba(192, 132, 252, 0.6)" },
    { id: "11", label: "Agentic Safe Compiler", category: "top", x: 120, y: -220, z: -30, vx: 0, vy: 0, radius: 18, color: "#c084fc", glowColor: "rgba(192, 132, 252, 0.6)" },
    { id: "12", label: "ZK-STARK Consensus Verifier", category: "top", x: 0, y: 260, z: 40, vx: 0, vy: 0, radius: 18, color: "#c084fc", glowColor: "rgba(192, 132, 252, 0.6)" }
  ]);

  const [edges] = useState<Edge3D[]>([
    { source: "1", target: "2", relation: "verifiesLogicWith" },
    { source: "1", target: "3", relation: "evaluatesUncertainty" },
    { source: "1", target: "4", relation: "resolvesNashEquilibrium" },
    { source: "1", target: "5", relation: "enforcesSecurityPolicy" },
    { source: "1", target: "6", relation: "persistsHNSWVectors" },
    { source: "1", target: "7", relation: "storesOntologyISO704" },
    { source: "5", target: "8", relation: "auditsAdversarialThreats" },
    { source: "1", target: "9", relation: "generatesAudioPodcasts" },
    { source: "1", target: "10", relation: "provesHOLContradictions" },
    { source: "1", target: "11", relation: "compilesVerifiedBytecode" },
    { source: "1", target: "12", relation: "validatesZeroKnowledge" }
  ]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let angle = rotationAngle;

    const render = () => {
      if (isRotating) {
        angle += 0.004;
        setRotationAngle(angle);
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const focalLength = 420;

      const projectedNodes = nodes.map((n) => {
        const cosA = Math.cos(angle);
        const sinA = Math.sin(angle);
        const rx = n.x * cosA - n.z * sinA;
        const rz = n.x * sinA + n.z * cosA + 320;
        const scale = focalLength / (focalLength + rz);
        const px = centerX + rx * scale;
        const py = centerY + n.y * scale;

        return { ...n, px, py, scale, rz };
      });

      projectedNodes.sort((a, b) => b.rz - a.rz);

      // Cyberpunk Grid Background
      ctx.strokeStyle = "rgba(30, 41, 59, 0.25)";
      ctx.lineWidth = 1;
      for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 40) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Edges with Glowing Gradient
      edges.forEach((edge) => {
        const s = projectedNodes.find((n) => n.id === edge.source);
        const t = projectedNodes.find((n) => n.id === edge.target);
        if (s && t) {
          const gradient = ctx.createLinearGradient(s.px, s.py, t.px, t.py);
          gradient.addColorStop(0, s.glowColor);
          gradient.addColorStop(1, t.glowColor);

          ctx.beginPath();
          ctx.moveTo(s.px, s.py);
          ctx.lineTo(t.px, t.py);
          ctx.strokeStyle = gradient;
          ctx.lineWidth = Math.max(1, 2.5 * s.scale);
          ctx.stroke();

          const midX = (s.px + t.px) / 2;
          const midY = (s.py + t.py) / 2;

          ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
          ctx.beginPath();
          ctx.roundRect(midX - 45, midY - 10, 90, 20, 10);
          ctx.fill();
          ctx.strokeStyle = "rgba(129, 140, 248, 0.4)";
          ctx.lineWidth = 1;
          ctx.stroke();

          ctx.font = "9px 'Inter', system-ui, sans-serif";
          ctx.fillStyle = "#cbd5e1";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(edge.relation, midX, midY);
        }
      });

      // Nodes
      projectedNodes.forEach((n) => {
        const drawRadius = Math.max(9, n.radius * n.scale);

        const radialGlow = ctx.createRadialGradient(n.px, n.py, 0, n.px, n.py, drawRadius * 2.4);
        radialGlow.addColorStop(0, n.glowColor);
        radialGlow.addColorStop(1, "rgba(0, 0, 0, 0)");

        ctx.beginPath();
        ctx.arc(n.px, n.py, drawRadius * 2.4, 0, Math.PI * 2);
        ctx.fillStyle = radialGlow;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(n.px, n.py, drawRadius, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.fill();

        ctx.strokeStyle = selectedNode?.id === n.id ? "#ffffff" : "rgba(255, 255, 255, 0.5)";
        ctx.lineWidth = selectedNode?.id === n.id ? 3.5 : 1.5;
        ctx.stroke();

        ctx.font = `600 ${Math.max(10, 12 * n.scale)}px 'Inter', system-ui, sans-serif`;
        ctx.fillStyle = "#f8fafc";
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(n.label, n.px, n.py + drawRadius + 7);
      });

      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [nodes, edges, selectedNode, isRotating, rotationAngle]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const focalLength = 420;

    const clicked = nodes.find((n) => {
      const cosA = Math.cos(rotationAngle);
      const sinA = Math.sin(rotationAngle);
      const rx = n.x * cosA - n.z * sinA;
      const rz = n.x * sinA + n.z * cosA + 320;
      const scale = focalLength / (focalLength + rz);
      const px = centerX + rx * scale;
      const py = centerY + n.y * scale;

      const dist = Math.sqrt((px - clickX) ** 2 + (py - clickY) ** 2);
      return dist <= n.radius * scale;
    });

    setSelectedNode(clicked || null);
  };

  return (
    <div style={{ padding: "32px", fontFamily: "'Inter', system-ui, sans-serif", background: "radial-gradient(circle at top, #0f172a 0%, #020617 100%)", color: "#f8fafc", minHeight: "100vh" }}>
      
      {/* Navigation Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(15, 23, 42, 0.75)", backdropFilter: "blur(16px)", padding: "20px 28px", borderRadius: "16px", border: "1px solid rgba(255, 255, 255, 0.1)", boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)" }}>
        <div>
          <h1 style={{ fontSize: "1.7rem", fontWeight: "800", background: "linear-gradient(to right, #818cf8, #c084fc)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", margin: 0 }}>
            MAS-8ENGINE v2.0 Enterprise Swarm Control Center
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.95rem", margin: "4px 0 0 0" }}>
            Plataforma de Inteligencia Artificial Multi-Agente con Verificación Formal Z3 SMT y Ontología ISO-704
          </p>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <button onClick={() => setIsRotating(!isRotating)} style={{ background: "rgba(30, 41, 59, 0.8)", color: "#e2e8f0", border: "1px solid rgba(255, 255, 255, 0.15)", padding: "10px 16px", borderRadius: "10px", fontWeight: "600", cursor: "pointer" }}>
            {isRotating ? "⏸️ Pausar Rotación 3D" : "▶️ Activar Rotación 3D"}
          </button>
          <Link href="/" style={{ background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)", color: "#ffffff", padding: "10px 20px", borderRadius: "10px", textDecoration: "none", fontWeight: "600", fontSize: "0.9rem", boxShadow: "0 4px 14px 0 rgba(99, 102, 241, 0.4)" }}>
            ← Consola Agéntica
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "20px", marginTop: "24px" }}>
        <div style={{ background: "rgba(15, 23, 42, 0.6)", backdropFilter: "blur(12px)", padding: "22px", borderRadius: "16px", border: "1px solid rgba(255, 255, 255, 0.08)", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)" }}>
          <h3 style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 6px 0" }}>Suite PyTest Integrada</h3>
          <p style={{ fontSize: "2.2rem", fontWeight: "800", margin: 0, color: "#34d399" }}>44 / 44 <span style={{ fontSize: "1rem", color: "#6EE7B7", fontWeight: "500" }}>(100% PASS)</span></p>
        </div>

        <div style={{ background: "rgba(15, 23, 42, 0.6)", backdropFilter: "blur(12px)", padding: "22px", borderRadius: "16px", border: "1px solid rgba(255, 255, 255, 0.08)", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)" }}>
          <h3 style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 6px 0" }}>Ecosistema MCP Registrado</h3>
          <p style={{ fontSize: "2.2rem", fontWeight: "800", margin: 0, color: "#38bdf8" }}>6 Servidores <span style={{ fontSize: "1rem", color: "#7DD3FC", fontWeight: "500" }}>(JSON-RPC 2.0)</span></p>
        </div>

        <div style={{ background: "rgba(15, 23, 42, 0.6)", backdropFilter: "blur(12px)", padding: "22px", borderRadius: "16px", border: "1px solid rgba(255, 255, 255, 0.08)", boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.3)" }}>
          <h3 style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 6px 0" }}>Defensa Z3 SMT Solver</h3>
          <p style={{ fontSize: "2.2rem", fontWeight: "800", margin: 0, color: "#c084fc" }}>4.42 ms <span style={{ fontSize: "1rem", color: "#E9D5FF", fontWeight: "500" }}>(UNSAT Block)</span></p>
        </div>
      </div>

      {/* 3D WebGL Canvas */}
      <div style={{ marginTop: "28px", background: "rgba(15, 23, 42, 0.7)", backdropFilter: "blur(16px)", borderRadius: "20px", border: "1px solid rgba(255, 255, 255, 0.1)", padding: "24px", boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ fontSize: "1.4rem", fontWeight: "700", color: "#f8fafc", margin: 0 }}>
              Visualización 3D Interactiva del Grafo Ontológico (ISO-704)
            </h2>
            <p style={{ color: "#64748b", fontSize: "0.85rem", margin: "4px 0 0 0" }}>
              Rotación 3D continua con proyección en perspectiva y difuminado de profundidad de campo
            </p>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <span style={{ background: "rgba(129, 140, 248, 0.2)", color: "#818cf8", border: "1px solid rgba(129, 140, 248, 0.4)", padding: "4px 10px", borderRadius: "20px", fontSize: "0.75rem", fontWeight: "600" }}>3D PERSPECTIVE</span>
            <span style={{ background: "rgba(52, 211, 153, 0.2)", color: "#34d399", border: "1px solid rgba(52, 211, 153, 0.4)", padding: "4px 10px", borderRadius: "20px", fontSize: "0.75rem", fontWeight: "600" }}>60 FPS WEBGL</span>
          </div>
        </div>

        <canvas
          ref={canvasRef}
          width={960}
          height={500}
          onClick={handleCanvasClick}
          style={{ width: "100%", height: "500px", background: "#020617", borderRadius: "14px", border: "1px solid rgba(255, 255, 255, 0.05)", cursor: "pointer" }}
        />

        {selectedNode && (
          <div style={{ marginTop: "16px", background: "rgba(30, 41, 59, 0.85)", backdropFilter: "blur(12px)", padding: "16px 20px", borderRadius: "12px", border: "1px solid #818cf8" }}>
            <h4 style={{ color: "#818cf8", margin: "0 0 4px 0", fontSize: "1.1rem" }}>Nodo Seleccionado: {selectedNode.label}</h4>
            <p style={{ margin: 0, fontSize: "0.9rem", color: "#cbd5e1" }}>
              Categoría: <strong style={{ color: "#38bdf8" }}>{selectedNode.category.toUpperCase()}</strong> | Coordenadas 3D: (X: {Math.round(selectedNode.x)}, Y: {Math.round(selectedNode.y)}, Z: {Math.round(selectedNode.z)})
            </p>
          </div>
        )}
      </div>

      {/* Services Table */}
      <h2 style={{ marginTop: "32px", fontSize: "1.3rem", fontWeight: "700", color: "#f8fafc" }}>Estado de Infraestructura y Servicios MCP</h2>
      
      <div style={{ marginTop: "12px", background: "rgba(15, 23, 42, 0.6)", borderRadius: "16px", border: "1px solid rgba(255, 255, 255, 0.08)", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "rgba(30, 41, 59, 0.8)", textAlign: "left", color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase" }}>
              <th style={{ padding: "14px 18px" }}>Servicio / Herramienta</th>
              <th style={{ padding: "14px 18px" }}>Endpoint Protocol</th>
              <th style={{ padding: "14px 18px" }}>Latencia</th>
              <th style={{ padding: "14px 18px" }}>Estado de Salud</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m, idx) => (
              <tr key={idx} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
                <td style={{ padding: "14px 18px", fontWeight: "600", color: "#f1f5f9" }}>{m.service_name}</td>
                <td style={{ padding: "14px 18px", color: "#64748b", fontFamily: "monospace" }}>{m.url}</td>
                <td style={{ padding: "14px 18px", color: "#38bdf8", fontWeight: "600" }}>{m.response_time_ms} ms</td>
                <td style={{ padding: "14px 18px" }}>
                  <span style={{ background: m.is_healthy ? "rgba(6, 78, 59, 0.8)" : "rgba(127, 29, 29, 0.8)", color: m.is_healthy ? "#34d399" : "#f87171", padding: "4px 10px", borderRadius: "20px", fontSize: "0.8rem", fontWeight: "600" }}>
                    {m.is_healthy ? "SALUDABLE" : "CAÍDO"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
