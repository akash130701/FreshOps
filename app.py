"""
FreshOps — weekly fruit & vegetable consumption schedule (Streamlit + PuLP).
"""

from __future__ import annotations

import html
import math
from pathlib import Path

import streamlit as st
from pulp import LpMinimize, LpProblem, LpStatus, LpVariable, lpSum, value

from shelf_life_db import lookup_shelf_life

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

_ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_SVG = _ASSETS / "logo.svg"


def inject_global_styles() -> None:
    """White canvas, clear type, subtle chrome — Streamlit layout overrides."""
    st.markdown(
        """
        <style>
          :root {
            --fo-bg: #ffffff;
            --fo-surface: #fafafa;
            --fo-border: #e5e7eb;
            --fo-text: #0f172a;
            --fo-muted: #64748b;
            --fo-accent: #15803d;
            --fo-accent-soft: #ecfdf5;
            --fo-radius: 10px;
            --fo-space: 8px;
          }
          .stApp {
            background-color: var(--fo-bg) !important;
          }
          [data-testid="stAppViewContainer"] > .main {
            background-color: var(--fo-bg);
          }
          section[data-testid="stSidebar"] {
            background-color: var(--fo-bg);
            border-right: 1px solid var(--fo-border);
          }
          section[data-testid="stSidebar"] > div {
            background-color: var(--fo-bg);
          }
          [data-testid="stHeader"] {
            background-color: var(--fo-bg);
            border-bottom: 1px solid var(--fo-border);
          }
          .main .block-container {
            padding-top: 1.75rem;
            padding-bottom: 3rem;
            max-width: 1120px;
          }
          /* Typography rhythm */
          .main h1, .main h2, .main h3 {
            color: var(--fo-text);
            font-weight: 600;
            letter-spacing: -0.02em;
          }
          .main p, .main li, .main span {
            color: var(--fo-text);
          }
          /* Instructions: black for readability */
          .main [data-testid="stCaption"],
          .main [data-testid="stCaption"] p,
          .main [data-testid="stCaption"] span {
            color: #000000 !important;
            opacity: 1 !important;
          }
          section[data-testid="stSidebar"] [data-testid="stCaption"],
          section[data-testid="stSidebar"] [data-testid="stCaption"] p {
            color: #000000 !important;
            opacity: 1 !important;
          }
          .main .stCaption p,
          section[data-testid="stSidebar"] .stCaption p {
            color: #000000 !important;
          }
          /* Primary actions */
          .stButton > button[kind="primary"] {
            border-radius: var(--fo-radius);
            font-weight: 600;
            padding: 0.5rem 1.1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
          }
          .stButton > button[kind="secondary"] {
            border-radius: var(--fo-radius);
          }
          /* Alerts — softer on white */
          div[data-testid="stSuccess"] {
            background-color: var(--fo-accent-soft);
            border: 1px solid #bbf7d0;
            border-radius: var(--fo-radius);
          }
          div[data-testid="stWarning"] {
            border-radius: var(--fo-radius);
          }
          div[data-testid="stError"] {
            border-radius: var(--fo-radius);
          }
          div[data-testid="stInfo"] {
            border-radius: var(--fo-radius);
            background-color: #f8fafc;
            border: 1px solid var(--fo-border);
          }
          /* Inputs */
          .stTextInput input, .stNumberInput input, div[data-baseweb="select"] {
            border-radius: 8px !important;
          }
          /* Expander */
          details {
            border: 1px solid var(--fo-border) !important;
            border-radius: var(--fo-radius) !important;
            background: var(--fo-bg) !important;
          }
          footer[data-testid="stFooter"] {
            visibility: hidden;
            min-height: 0 !important;
            padding: 0 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header() -> None:
    """Logo + title row."""
    c_logo, c_text = st.columns([0.6, 5], gap="small")
    with c_logo:
        if LOGO_SVG.exists():
            st.image(str(LOGO_SVG), width=72)
        else:
            st.markdown("### 🥬")
    with c_text:
        st.markdown(
            """
            <style>
              .fo-brand-block {
                font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
              }
              .fo-brand-title {
                display: inline-block;
                margin: 0 0 10px 0;
                padding-bottom: 8px;
                border-bottom: 4px solid #15803d;
                font-size: clamp(2.1rem, 5.5vw, 3rem);
                font-weight: 800;
                color: #000000;
                letter-spacing: -0.045em;
                line-height: 1.1;
              }
              .fo-brand-sub {
                margin: 0 0 32px 0;
                color: #000000;
                font-size: 1rem;
                line-height: 1.5;
                font-weight: 500;
                max-width: 42em;
              }
            </style>
            <div class="fo-brand-block">
              <div class="fo-brand-title">FreshOps</div>
              <p class="fo-brand-sub">Your weekly produce plan</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_schedule_calendar(sched: dict[str, dict[str, int]]) -> None:
    """Calendar-style grid: columns = days, rows = produce + totals row."""
    items = list(sched.keys())
    esc = html.escape

    day_long = {
        "Mon": "Monday",
        "Tue": "Tuesday",
        "Wed": "Wednesday",
        "Thu": "Thursday",
        "Fri": "Friday",
        "Sat": "Saturday",
        "Sun": "Sunday",
    }

    head_cells = []
    for d in DAYS:
        wk = " fo-wknd-h" if d in ("Sat", "Sun") else ""
        title = day_long[d]
        head_cells.append(
            f'<div class="fo-hcell{wk}" title="{esc(title)}">{esc(d)}</div>'
        )

    body_rows = []
    for j, item in enumerate(items):
        alt = " fo-row-alt" if j % 2 == 1 else ""
        cells = [f'<div class="fo-itemcell">{esc(item)}</div>']
        for d in DAYS:
            v = int(sched[item].get(d, 0))
            z = " fo-empty" if v == 0 else ""
            inner = "—" if v == 0 else str(v)
            cells.append(f'<div class="fo-datacell{z}">{inner}</div>')
        body_rows.append(f'<div class="fo-row{alt}">{"".join(cells)}</div>')

    tot_cells = ['<div class="fo-tlabel">Daily total</div>']
    for d in DAYS:
        t = sum(int(sched[it].get(d, 0)) for it in items)
        wk = " fo-wknd-h" if d in ("Sat", "Sun") else ""
        tot_cells.append(f'<div class="fo-totalcell{wk}">{t}</div>')

    css = """
    <style>
    .fo-cal-wrap {
      font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #e5e7eb;
      background: #ffffff;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
      margin-top: 8px;
    }
    .fo-cal-head {
      display: grid;
      grid-template-columns: minmax(140px, 1.35fr) repeat(7, minmax(0, 1fr));
      background: #fafafa;
      color: #0f172a;
      border-bottom: 3px solid #15803d;
      font-weight: 600;
      font-size: 0.8125rem;
      letter-spacing: 0.02em;
    }
    .fo-corner {
      padding: 14px 16px;
      display: flex;
      align-items: center;
      border-right: 1px solid #e5e7eb;
      background: #ffffff;
    }
    .fo-corner span {
      font-size: 0.6875rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #64748b;
    }
    .fo-hcell {
      padding: 12px 6px;
      text-align: center;
      border-left: 1px solid #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      font-size: 0.875rem;
      font-weight: 600;
      color: #334155;
    }
    .fo-wknd-h { background: #f1f5f9; color: #475569; }
    .fo-row {
      display: grid;
      grid-template-columns: minmax(140px, 1.35fr) repeat(7, minmax(0, 1fr));
      border-top: 1px solid #e5e7eb;
      background: #ffffff;
    }
    .fo-row.fo-row-alt { background: #fafafa; }
    .fo-row.fo-row-alt .fo-itemcell, .fo-row.fo-row-alt .fo-datacell { background: transparent; }
    .fo-itemcell {
      padding: 12px 14px;
      font-weight: 600;
      color: #0f172a;
      font-size: 0.875rem;
      line-height: 1.35;
      border-right: 1px solid #e5e7eb;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .fo-datacell {
      padding: 12px 8px;
      text-align: center;
      font-variant-numeric: tabular-nums;
      font-size: 0.9375rem;
      color: #0f172a;
      font-weight: 500;
      border-left: 1px solid #f1f5f9;
    }
    .fo-datacell.fo-empty { color: #cbd5e1; font-weight: 400; }
    .fo-total-row {
      border-top: 2px solid #e5e7eb !important;
      background: #fafafa !important;
    }
    .fo-tlabel {
      padding: 12px 14px;
      font-weight: 700;
      color: #0f172a;
      font-size: 0.8125rem;
      border-right: 1px solid #e5e7eb;
      background: #ffffff;
    }
    .fo-totalcell {
      padding: 12px 8px;
      text-align: center;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      color: #15803d;
      font-size: 0.9375rem;
      background: #fafafa;
      border-left: 1px solid #f1f5f9;
    }
    .fo-totalcell.fo-wknd-h { background: #f1f5f9; }
    </style>
    """

    head_html = (
        '<div class="fo-cal-wrap">'
        '<div class="fo-cal-head">'
        '<div class="fo-corner"><span>Produce</span></div>'
        + "".join(head_cells)
        + "</div>"
    )
    foot_html = (
        '<div class="fo-row fo-total-row">'
        + "".join(tot_cells)
        + "</div></div>"
    )

    st.markdown(
        css + head_html + "".join(body_rows) + foot_html,
        unsafe_allow_html=True,
    )


def expiry_days_to_eidx(expiry_days: float) -> tuple[int, str | None]:
    """
    Shelf life in whole days from the start of the week (Monday = day 1).
    Returns (last_day_index 0..6, error_message or None).
    """
    if expiry_days <= 0:
        return 0, "Expiry must be a positive number of days."
    n = max(1, min(7, int(math.ceil(float(expiry_days)))))
    return n - 1, None


def parse_item_expiry_days(it: dict) -> float | None:
    """Reads expiry_days, or legacy expiry_day weekday string from session state."""
    if "expiry_days" in it:
        try:
            return float(it["expiry_days"])
        except (TypeError, ValueError):
            return None
    ed = it.get("expiry_day")
    if isinstance(ed, str) and ed in DAYS:
        return float(DAYS.index(ed) + 1)
    return None


def build_schedule(items: list[dict]) -> tuple[dict, dict, str]:
    """
    items: list of {"name": str, "qty": int, "expiry_days": float}

    Returns (schedule[item_name][day] = int qty, meta, status_message)
    """
    if not items:
        return {}, {}, "Add at least one item."

    prob = LpProblem("FreshOps", LpMinimize)
    x: dict[tuple[int, int], LpVariable] = {}
    dev_p: dict[tuple[int, int], LpVariable] = {}
    dev_n: dict[tuple[int, int], LpVariable] = {}
    eidx_per_item: list[int] = []

    for i, it in enumerate(items):
        name = it["name"].strip() or f"Item {i+1}"
        qty = int(it["qty"])
        raw_exp = parse_item_expiry_days(it)
        if raw_exp is None:
            return {}, {}, f"“{name}”: enter expiry as a number of days (or remove and re-add the item)."
        eidx, err = expiry_days_to_eidx(raw_exp)
        if err:
            return {}, {}, f"“{name}”: {err}"
        if qty <= 0:
            return {}, {}, f"Quantity for “{name}” must be positive."
        eidx_per_item.append(eidx)
        n_days = eidx + 1
        target = qty / n_days

        for d in range(eidx + 1):
            x[(i, d)] = LpVariable(f"x_{i}_{d}", lowBound=0, cat="Integer")
            dev_p[(i, d)] = LpVariable(f"dp_{i}_{d}", lowBound=0)
            dev_n[(i, d)] = LpVariable(f"dn_{i}_{d}", lowBound=0)
            prob += x[(i, d)] - target == dev_p[(i, d)] - dev_n[(i, d)]

        prob += lpSum(x[(i, d)] for d in range(eidx + 1)) == qty

    prob += lpSum(dev_p[k] + dev_n[k] for k in dev_p)

    prob.solve()

    status = LpStatus[prob.status]
    if prob.status != 1:
        return {}, {}, f"Solver status: {status}. Try adjusting quantities or expiry days."

    def row_label(i: int, raw: str) -> str:
        base = raw.strip() or f"Item {i+1}"
        same = sum(
            1
            for j, o in enumerate(items)
            if (o["name"].strip() or f"Item {j+1}") == base and j <= i
        )
        return f"{base} ({same})" if same > 1 else base

    def as_int(v: object) -> int:
        if v is None:
            return 0
        return int(round(float(v)))

    schedule: dict[str, dict[str, int]] = {}
    for i, it in enumerate(items):
        name = row_label(i, it["name"])
        eidx = eidx_per_item[i]
        schedule[name] = {}
        for d in range(len(DAYS)):
            if d <= eidx:
                schedule[name][DAYS[d]] = as_int(value(x[(i, d)]))
            else:
                schedule[name][DAYS[d]] = 0

    return schedule, {}, f"Optimal ({status}). Whole units per day, spread as evenly as possible before expiry."


def main() -> None:
    st.set_page_config(
        page_title="FreshOps",
        page_icon="🥬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_styles()
    render_brand_header()
    # st.caption(
    #     "Plan how much of each fruit or vegetable to eat **Mon–Sun**, so you finish each item "
    #     "before it spoils. **Shelf life** can come from the built-in produce database (estimates) or "
    #     "your own number of days from Monday (1 = Monday only, 7 = full week). "
    #     "Consumption is spread evenly in whole units."
    # )
    st.markdown(
    """
    <p style="color: #000000;">
    Plan how much of each fruit or vegetable to eat <b>Mon–Sun</b>, so you finish each item
    before it spoils. <b>Shelf life</b> can come from the built-in produce database (estimates) or
    your own number of days from Monday (1 = Monday only, 7 = full week).
    Consumption is spread evenly in whole units.
    </p>
    """,
    unsafe_allow_html=True,
)
    st.divider()

    if "produce_list" not in st.session_state:
        st.session_state.produce_list = []

    with st.sidebar:
        sb_logo, sb_title = st.columns([1, 3])
        with sb_logo:
            if LOGO_SVG.exists():
                st.image(str(LOGO_SVG), width=44)
        with sb_title:
            st.markdown("**FreshOps**")
        st.subheader("Add produce")
        name = st.text_input("Name", placeholder="e.g. Spinach")
        qty = st.number_input("Total quantity (your unit)", min_value=1, value=1, step=1)

        shelf_mode = st.radio(
            "Shelf life",
            ["Database", "Custom"],
            horizontal=True,
            help="Database uses typical shelf-life estimates for common produce. Custom lets you enter days yourself.",
        )

        expiry_days = 4.0
        if shelf_mode == "Custom":
            expiry_days = st.number_input(
                "Shelf life (days from Monday)",
                min_value=1.0,
                max_value=14.0,
                value=4.0,
                step=1.0,
                help="How many days the item stays good starting this Monday. Values above 7 are capped at a full week in the schedule.",
            )
        else:
            st.caption(
                "Uses the **built-in list** of typical fridge/pantry life (rough estimates). "
                "Not a substitute for labels or food-safety rules."
            )
            if name.strip():
                sl_preview = lookup_shelf_life(name.strip())
                if sl_preview.days is not None:
                    st.success(
                        f"**~{sl_preview.days} days** — matched as *{sl_preview.matched_name}*"
                    )
                else:
                    st.warning(
                        "No close match in the database. Try another spelling, pick from suggestions "
                        "when you add, or switch to **Custom**."
                    )
                    if sl_preview.suggestions:
                        st.caption("Examples in DB: " + ", ".join(sl_preview.suggestions[:12]) + " …")

        if st.button("Add item", type="primary"):
            if not name.strip():
                st.warning("Enter a name.")
            elif qty <= 0:
                st.warning("Quantity must be positive.")
            elif shelf_mode == "Database":
                sl = lookup_shelf_life(name.strip())
                if sl.days is None:
                    sug = ", ".join(sl.suggestions[:6]) if sl.suggestions else "(see shelf_life_db.py)"
                    st.error(
                        f'Could not match “{name.strip()}”. Try a different name, or use **Custom**. '
                        f"Examples: {sug}"
                    )
                else:
                    st.session_state.produce_list.append(
                        {
                            "name": name.strip(),
                            "qty": int(qty),
                            "expiry_days": float(sl.days),
                            "shelf_life_source": "database",
                            "db_matched_name": sl.matched_name,
                        }
                    )
                    st.rerun()
            else:
                st.session_state.produce_list.append(
                    {
                        "name": name.strip(),
                        "qty": int(qty),
                        "expiry_days": float(expiry_days),
                        "shelf_life_source": "custom",
                    }
                )
                st.rerun()

        st.divider()
        st.subheader("Your list")
        if not st.session_state.produce_list:
            st.info("No items yet.")
        else:
            for idx, it in enumerate(st.session_state.produce_list):
                c1, c2 = st.columns([3, 1])
                with c1:
                    ed = it.get("expiry_days")
                    if ed is None and it.get("expiry_day"):
                        ed = parse_item_expiry_days(it)
                    src = it.get("shelf_life_source", "custom")
                    src_lbl = "DB" if src == "database" else "custom"
                    extra = ""
                    if src == "database" and it.get("db_matched_name"):
                        extra = f" (*{it['db_matched_name']}*)"
                    ed_disp = f"{ed:g} day(s) · {src_lbl}{extra}" if ed is not None else "? days"
                    st.write(f"**{it['name']}** — {it['qty']} — use within **{ed_disp}**")
                with c2:
                    if st.button("Remove", key=f"rm_{idx}"):
                        st.session_state.produce_list.pop(idx)
                        st.rerun()

        if st.button("Clear all"):
            st.session_state.produce_list = []
            st.rerun()

    col1, col2 = st.columns([2, 1])
    with col1:
        gen = st.button("Generate schedule", type="primary", disabled=len(st.session_state.produce_list) == 0)

    if gen:
        schedule, _, msg = build_schedule(st.session_state.produce_list)
        st.session_state.last_msg = msg
        st.session_state.last_schedule = schedule

    if "last_msg" in st.session_state:
        if "Optimal" in st.session_state.last_msg:
            st.success(st.session_state.last_msg)
        elif st.session_state.last_msg:
            st.warning(st.session_state.last_msg)

    sched = st.session_state.get("last_schedule")
    if sched:
        st.subheader("Weekly consumption calendar")
        st.caption(
            "Days across the top — units per day. **Sat** and **Sun** use a light gray header band for quick scanning."
        )
        render_schedule_calendar(sched)

        st.subheader("Totals check")
        sched_keys = list(sched.keys())
        for idx, it in enumerate(st.session_state.produce_list):
            n = sched_keys[idx] if idx < len(sched_keys) else it["name"].strip() or it["name"]
            s = sum(int(sched.get(n, {}).get(d, 0)) for d in DAYS)
            st.write(f"**{n}**: scheduled total = **{s}** (target **{int(it['qty'])}**)")

        with st.expander("How it works"):
            st.markdown(
                """
                For each item, **shelf life** is the number of days from **Monday** of this plan (day 1 =
                Monday only, day 7 = through Sunday). You only consume that item on those days. The
                model **minimizes unevenness** using **whole units per day** (integer variables) —
                as close as possible to an even split. More than 7 days is treated as 7 for this weekly
                schedule.

                **Database** mode uses a fixed list of typical storage lives (rough estimates); **Custom**
                uses the number you enter. Estimates are not medical or food-safety advice — follow
                packaging, local guidance, and your own judgment.
                """
            )


if __name__ == "__main__":
    main()
