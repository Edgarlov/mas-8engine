# Codex operating contract — KBS-TECH

Goal: unblock and execute M7, a controlled comparison of the same LLM/configuration:
A = model without KBS context
B = same model with KBS context.

Hard constraints:
1. Do not change frozen RC1 semantics to improve benchmark results.
2. Do not let either branch see the other branch output.
3. Use the exact same reserved tasks, model and observable generation settings.
4. Preserve raw prompts, raw outputs, model identifier, observable settings, elapsed time and available usage.
5. Branch B may receive only KBS context in addition to the same task prompt.
6. Never convert an inferred claim into a sourced fact.
7. Unknown or unsupported answers must be measurable as such.
8. If a real model provider cannot be configured, stop with BLOCKED_PROVIDER rather than simulate outputs.

Acceptance:
Produce artifacts/m7/results.json and artifacts/m7/report.md.
No claim of superiority unless supported by the frozen rubric.
