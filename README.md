# KBS-TECH

Federated knowledge-based system prototype for traceable AI/software knowledge.

Current validated milestones:
- M1 architecture
- M2 eight Domain-KBS minimum
- M3 end-to-end federation
- M4 RC1 hardening: 14/14 development checks
- M5 reserved internal evaluation: 10/10
- M6 simple-baseline utility: demonstrated value for traceability and change control
- M7 controlled LLM vs LLM+KBS benchmark: pending execution

## Codex task
Implement and run M7 without changing the frozen RC1 semantics. Use the same model/configuration for both branches. Branch A receives no KBS context. Branch B receives KBS context. Preserve exact inputs/outputs/configuration and report correctness, unsupported claims, abstention, traceability, critical errors, observable time and available usage metrics.

Do not claim general superiority unless the controlled A/B evidence supports it.
