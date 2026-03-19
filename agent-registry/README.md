# Agent Registry

This folder holds the strict JSON contracts defining individual auditing and fixing agents.

Whenever the Coordinator summons a Swarm subagent, it passes the exact `auditRules` and `outputSchema` bounded within these contracts into the Qwen System Prompt context window.
