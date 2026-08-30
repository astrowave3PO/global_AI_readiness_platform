import streamlit as st
from datetime import date

from readiness_engine import assess_all_sites, rank_rollout_sites


st.set_page_config(
    page_title="Global AI Platform Readiness",
    layout="wide",
)

PROGRAM_BUFFER_DAYS = 14

# ---------- Load deterministic program state ----------
assessments = assess_all_sites()
ranking = rank_rollout_sites()

by_site = {site["site_id"]: site for site in assessments}

ready_sites = [
    site for site in assessments
    if site["readiness_status"] == "READY"
]

on_track_sites = [
    site for site in assessments
    if site["readiness_status"] == "NOT_READY"
    and site["schedule_status"] == "ON_TRACK"
]

at_risk_sites = [
    site for site in assessments
    if site["schedule_status"] == "AT_RISK"
]


def schedule_buffer_days(site):
    blocker = site["critical_blocker"]
    if not blocker:
        return None

    planned = date.fromisoformat(site["planned_deploy_date"])
    resolution = date.fromisoformat(blocker["target_resolution_date"])
    return (planned - resolution).days


def blocker_owners(site):
    owners = []
    for blocker in site["blockers"]:
        owner = blocker["owner"]
        if owner not in owners:
            owners.append(owner)
    return " + ".join(owners) if owners else "Deployment TPM / site team"


# ---------- Header ----------
st.title("Global AI Platform Readiness")
st.caption(
    "Vera Rubin NVL72 | V1 prototype | Synthetic / non-confidential site data"
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Sites assessed", len(assessments))
m2.metric("Ready", len(ready_sites))
m3.metric("Not ready, on track", len(on_track_sites))
m4.metric("At risk", len(at_risk_sites))


# ---------- Executive rollout view ----------
st.subheader("Proposed rollout plan")
st.caption(
    "TPM recommendation based on the deterministic readiness and schedule states below."
)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### Wave 1")
    if ready_sites:
        for site in sorted(ready_sites, key=lambda x: x["planned_deploy_date"]):
            st.success(
                f'**{site["site_id"]}** — READY | '
                f'Planned {site["planned_deploy_date"]}'
            )
    else:
        st.write("No sites currently ready.")

with c2:
    st.markdown("### Wave 2 candidate")
    if on_track_sites:
        for site in sorted(on_track_sites, key=lambda x: x["planned_deploy_date"]):
            gates = ", ".join(site["failed_gates"])
            st.warning(
                f'**{site["site_id"]}** — ON TRACK | '
                f'Close {gates}'
            )
    else:
        st.write("No on-track candidates.")

with c3:
    st.markdown("### Blocked / at risk")
    if at_risk_sites:
        for site in sorted(at_risk_sites, key=lambda x: x["planned_deploy_date"]):
            blocker = site["critical_blocker"]
            blocker_text = (
                f'{blocker["gate"]} — {blocker["target_resolution_date"]}'
                if blocker else "Timing unresolved"
            )
            st.error(
                f'**{site["site_id"]}** — AT RISK | {blocker_text}'
            )
    else:
        st.write("No sites currently at risk.")


# ---------- Changes since last review ----------
st.subheader("Changes since last review")
st.info("Baseline review — no prior snapshot available.")


# ---------------------------------------------------------
# VERA RUBIN PLATFORM CONTEXT
# ---------------------------------------------------------

st.subheader("Vera Rubin NVL72 - Platform Context")

st.caption(
    "What changes with the platform, and what that means for site readiness."
)

with st.expander("Why Vera Rubin changes the readiness bar", expanded=True):

    st.markdown("""
Vera Rubin is introduced as a **rack-scale AI system**, not simply as a GPU refresh.
That shifts readiness from having individual components available to having the
**full rack, facility and operational path ready together**.
""")

    platform_context = [
        {
            "Platform change": "Rack-scale system",
            "Readiness implication": "A complete, qualified rack becomes the deployment unit — server availability alone is not enough.",
            "Primary gates": "SUPPLY · PLATFORM",
        },
        {
            "Platform change": "Higher rack power density",
            "Readiness implication": "Validate usable power at the rack, including the distribution path. 800V DC is an emerging architecture.",
            "Primary gates": "POWER",
        },
        {
            "Platform change": "Direct liquid cooling",
            "Readiness implication": "Confirm the full thermal path can support the rack — cold plates, rack plumbing, CDU, facility cooling and Ops.",
            "Primary gates": "COOLING · OPERATIONS",
        },
        {
            "Platform change": "NVLink scale-up + scale-out fabric",
            "Readiness implication": "Installed networking is not sufficient; topology and end-to-end connectivity need to be qualified before capacity is released.",
            "Primary gates": "NETWORK",
        },
        {
            "Platform change": "Integrated platform qualification",
            "Readiness implication": "Hardware onsite does not equal usable capacity. Platform validation, firmware, health checks and operating readiness must close before deployment.",
            "Primary gates": "PLATFORM · OPERATIONS",
        },
    ]

    st.dataframe(
        platform_context,
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Prototype note: site data, deployment dates and the 200 kW/rack threshold are "
    "assumptions. Public Vera Rubin architecture is used only to frame the readiness model."
)




# ---------- Readiness matrix ----------
st.subheader("Readiness matrix")

matrix_rows = []
for site in assessments:
    matrix_rows.append(
        {
            "Site": site["site_id"],
            "Power": "✅" if site["gates"]["POWER"] else "❌",
            "Cooling": "✅" if site["gates"]["COOLING"] else "❌",
            "Network": "✅" if site["gates"]["NETWORK"] else "❌",
            "Supply": "✅" if site["gates"]["SUPPLY"] else "❌",
            "Platform": "✅" if site["gates"]["PLATFORM"] else "❌",
            "Operations": "✅" if site["gates"]["OPERATIONS"] else "❌",
            "Readiness": site["readiness_status"],
            "Schedule": site["schedule_status"],
        }
    )

st.dataframe(
    matrix_rows,
    use_container_width=True,
    hide_index=True,
)


# ---------- Rollout sequence ----------
st.subheader("Proposed rollout sequence")
st.caption(
    "Ordering is produced by deterministic readiness / schedule rules. "
    "Wave grouping remains a TPM recommendation."
)

ranking_rows = []
for site in ranking:
    blocker = site["critical_blocker"]
    ranking_rows.append(
        {
            "Order": site["rank"],
            "Site": site["site_id"],
            "Readiness": site["readiness_status"],
            "Schedule": site["schedule_status"],
            "Priority": site["program_priority"],
            "Planned deployment": site["planned_deploy_date"],
            "Failed gates": ", ".join(site["failed_gates"]) or "—",
            "Critical blocker": (
                f'{blocker["gate"]} — {blocker["target_resolution_date"]}'
                if blocker else "—"
            ),
        }
    )

st.dataframe(
    ranking_rows,
    use_container_width=True,
    hide_index=True,
)


# ---------- Technical blockers ----------
st.subheader("Top technical blockers")

blocker_rows = []
for site in assessments:
    for blocker in site["blockers"]:
        blocker_rows.append(
            {
                "Site": site["site_id"],
                "Gate": blocker["gate"],
                "Blocker": blocker["description"],
                "Owner": blocker["owner"],
                "Target resolution": blocker["target_resolution_date"],
                "Schedule": site["schedule_status"],
                "Deployment impact": site["deployment_impact"],
            }
        )

blocker_rows = sorted(
    blocker_rows,
    key=lambda row: (
        0 if row["Schedule"] == "AT_RISK" else 1,
        row["Target resolution"],
    )
)

if blocker_rows:
    st.dataframe(
        blocker_rows,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success("No open blockers.")


# ---------- Critical-path dependencies ----------
st.subheader("Critical-path dependencies")
st.caption(
    "V1 approximation: the latest unresolved blocker is treated as the controlling dependency."
)

critical_rows = []
for site in assessments:
    blocker = site["critical_blocker"]
    if blocker:
        critical_rows.append(
            {
                "Site": site["site_id"],
                "Critical dependency": blocker["gate"],
                "Owner": blocker["owner"],
                "Target resolution": blocker["target_resolution_date"],
                "Planned deployment": site["planned_deploy_date"],
                "Buffer days": schedule_buffer_days(site),
                "Schedule": site["schedule_status"],
            }
        )

if critical_rows:
    st.dataframe(
        critical_rows,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success("No unresolved critical dependencies.")


# ---------- Decisions required ----------
st.subheader("Decisions required")

if at_risk_sites:
    for site in sorted(at_risk_sites, key=lambda x: x["planned_deploy_date"]):
        blocker = site["critical_blocker"]
        buffer_days = schedule_buffer_days(site)

        if blocker:
            st.markdown(
                f'**{site["site_id"]} — {blocker["gate"]}:** '
                f'{blocker["description"]} '
                f'Target resolution is **{blocker["target_resolution_date"]}** '
                f'vs. planned deployment **{site["planned_deploy_date"]}** — '
                f'**{buffer_days}-day buffer vs. {PROGRAM_BUFFER_DAYS}-day program requirement.** '
                f'**Decision:** pull in the dependency, explicitly accept the reduced buffer, '
                f'or rebaseline the site.'
            )
        else:
            st.markdown(
                f'**{site["site_id"]}:** failed readiness gates exist without a '
                f'credible recovery date. **Decision:** establish an owned recovery plan '
                f'before committing the deployment.'
            )
else:
    st.success("No leadership decisions currently required.")


# ---------- Recommended actions ----------
st.subheader("Recommended actions")

action_rows = []

for site in assessments:
    if site["readiness_status"] == "READY":
        action = "Proceed to deployment qualification."
    elif site["schedule_status"] == "ON_TRACK":
        action = (
            f'Close {", ".join(site["failed_gates"])} gates and protect the current recovery dates.'
        )
    else:
        blocker = site["critical_blocker"]
        if blocker:
            action = (
                f'Escalate {blocker["gate"]} recovery options and rebaseline if the date cannot be pulled in.'
            )
        else:
            action = "Establish blocker owner and recovery date before committing deployment."

    action_rows.append(
        {
            "Site": site["site_id"],
            "Owner / focus": blocker_owners(site),
            "Action": action,
            "Planned deployment": site["planned_deploy_date"],
        }
    )

st.dataframe(
    action_rows,
    use_container_width=True,
    hide_index=True,
)


# ---------- Traceability ----------
st.subheader("Traceability")
st.caption("Important claims below are directly traceable to the structured program data.")

for site in ranking:
    result = by_site[site["site_id"]]

    with st.expander(f'{result["site_id"]} — source facts'):
        st.json(
            {
                "readiness_status": result["readiness_status"],
                "schedule_status": result["schedule_status"],
                "planned_deploy_date": result["planned_deploy_date"],
                "program_priority": result["program_priority"],
                "gates": result["gates"],
                "failed_gates": result["failed_gates"],
                "blockers": result["blockers"],
                "critical_blocker": result["critical_blocker"],
            }
        )


st.info(
    "Readiness and schedule calculations are deterministic. "
    "Rollout-wave grouping, trade-off explanations, and leadership recommendations "
    "are program-management judgments layered on top of those facts."
)
