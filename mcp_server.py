from mcp.server import MCPServer

from readiness_engine import (
    assess_site_readiness as assess_readiness_engine,
    rank_rollout_sites as rank_rollout_engine,
)

mcp = MCPServer(
    "Global AI Scaling Readiness Copilot",
    instructions=(
        "Use structured site and platform data as the source of truth. "
        "Do not invent infrastructure facts, dates, dependencies, or commitments. "
        "Readiness outputs are deterministic facts; rollout recommendations are advisory."
    ),
)

@mcp.tool(title="Assess site readiness")
def assess_site_readiness(
    site_id: str,
    platform_id: str = "VERA_RUBIN_NVL72",
) -> dict:
    """Deterministically assess one datacenter site's readiness."""
    return assess_readiness_engine(site_id, platform_id)

@mcp.tool(title="Rank rollout sites")
def rank_rollout_sites(
    platform_id: str = "VERA_RUBIN_NVL72",
) -> list[dict]:
    """Return a deterministic rollout ordering; this is not the final TPM wave decision."""
    return rank_rollout_engine(platform_id)
