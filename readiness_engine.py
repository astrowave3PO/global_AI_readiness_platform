from datetime import date
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

SCHEDULE_RANK = {
    "READY": 0,
    "ON_TRACK": 1,
    "AT_RISK": 2,
}

def _load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

def load_platform(platform_id):
    platform = _load_json("platform.json")
    if platform["platform_id"] != platform_id:
        raise ValueError(f"Unknown platform_id: {platform_id}")
    return platform

def load_site(site_id):
    for site in _load_json("sites.json"):
        if site["site_id"] == site_id:
            return site
    raise ValueError(f"Unknown site_id: {site_id}")

def _schedule_status(site, blockers):
    if not blockers:
        return "READY"

    planned = date.fromisoformat(site["planned_deploy_date"])
    latest = max(date.fromisoformat(b["target_resolution_date"]) for b in blockers)
    buffer_days = (planned - latest).days
    return "ON_TRACK" if buffer_days >= 14 else "AT_RISK"

def assess_site_readiness(site_id, platform_id="VERA_RUBIN_NVL72"):
    platform = load_platform(platform_id)
    site = load_site(site_id)
    req = platform["requirements"]

    gates = {
        "POWER": site["power"]["usable_power_kw_per_rack"] >= req["power"]["required_usable_power_kw_per_rack"],
        "COOLING": site["cooling"]["usable_cooling_kw_per_rack"] >= req["cooling"]["required_usable_cooling_kw_per_rack"],
        "NETWORK": site["network"]["network_qualified"] == req["network"]["network_qualified_required"],
        "SUPPLY": site["supply"]["complete_racks_available"] >= req["supply"]["required_complete_racks"],
        "PLATFORM": site["platform"]["platform_qualified"] == req["platform"]["platform_qualified_required"],
        "OPERATIONS": site["operations"]["ops_ready"] == req["operations"]["ops_ready_required"],
    }

    failed_gates = [gate for gate, passed in gates.items() if not passed]
    blockers = [b for b in site.get("blockers", []) if b["gate"] in failed_gates]

    readiness_status = "READY" if not failed_gates else "NOT_READY"
    schedule_status = _schedule_status(site, blockers)
    critical_blocker = max(blockers, key=lambda b: b["target_resolution_date"]) if blockers else None

    return {
        "site_id": site_id,
        "platform_id": platform_id,
        "readiness_status": readiness_status,
        "schedule_status": schedule_status,
        "planned_deploy_date": site["planned_deploy_date"],
        "program_priority": site["program_priority"],
        "gates": gates,
        "failed_gates": failed_gates,
        "blockers": blockers,
        "critical_blocker": critical_blocker,
        "deployment_impact": (
            "Can proceed to deployment qualification."
            if readiness_status == "READY"
            else (
                "Current blockers threaten the planned deployment date."
                if schedule_status == "AT_RISK"
                else "Not ready today, but current blocker dates preserve schedule."
            )
        ),
    }

def assess_all_sites(platform_id="VERA_RUBIN_NVL72"):
    return [
        assess_site_readiness(site["site_id"], platform_id)
        for site in _load_json("sites.json")
    ]

def _rollout_sort_key(result):
    planned_date = date.fromisoformat(result["planned_deploy_date"])

    if result["readiness_status"] == "READY":
        return (
            0,
            planned_date,
            -result["program_priority"],
        )

    critical = result["critical_blocker"]
    blocker_date = (
        date.fromisoformat(critical["target_resolution_date"])
        if critical else date.max
    )

    return (
        1,
        SCHEDULE_RANK[result["schedule_status"]],
        blocker_date,
        -result["program_priority"],
        planned_date,
    )

def rank_rollout_sites(platform_id="VERA_RUBIN_NVL72"):
    ranked = sorted(
        assess_all_sites(platform_id),
        key=_rollout_sort_key,
    )

    results = []
    for rank, site in enumerate(ranked, start=1):
        results.append(
            {
                "rank": rank,
                "site_id": site["site_id"],
                "readiness_status": site["readiness_status"],
                "schedule_status": site["schedule_status"],
                "program_priority": site["program_priority"],
                "planned_deploy_date": site["planned_deploy_date"],
                "failed_gates": site["failed_gates"],
                "critical_blocker": site["critical_blocker"],
            }
        )
    return results
