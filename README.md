# Global AI Scaling Readiness Copilot

A lightweight interview-learning prototype that models readiness to introduce a new rack-scale AI platform across a synthetic global datacenter footprint.

## What it demonstrates

- Six readiness gates: Power, Cooling, Network, Supply, Platform, Operations
- Deterministic site readiness assessment
- Schedule health and blocker ownership
- Transparent rollout ranking
- TPM-style readiness dashboard
- Optional MCP tools for AI-assisted executive review

## Architecture

```text
Synthetic platform + site data
            |
            v
Deterministic Python readiness engine
          /   \
         /     \
 Streamlit UI   MCP tools
                   |
                   v
              LLM / Copilot
```

## Important design principle

Infrastructure facts and readiness gates are deterministic. The LLM is used for synthesis, trade-off explanations, questions for human investigation, and recommendations. It is not allowed to invent infrastructure facts or override readiness gates.

## Run the dashboard locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Data

All site data is synthetic and non-confidential. The Vera Rubin values used in the readiness model include simplified prototype assumptions for interview learning and should not be interpreted as Microsoft design requirements.

## Optional MCP demo

Install the MCP dependencies:

```bash
python -m pip install -r requirements-mcp.txt
mcp dev mcp_server.py
```

The server exposes:

- `assess_site_readiness(site_id, platform_id)`
- `rank_rollout_sites(platform_id)`

## V1 scope

This is intentionally small. It does not connect to production systems, implement real-time telemetry, or perform datacenter engineering design.
