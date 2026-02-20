import os
import urllib.request
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Credit to sfc-gh-tteixeira on dashboard template
# Github: https://github.com/streamlit/demo-stockpeers/blob/main/streamlit_app.py
# Streamlit: https://demo-stockpeers.streamlit.app/?ref=streamlit-io-gallery-favorites&stocks=AAPL%2CMSFT%2CGOOGL%2CNVDA%2CAMZN%2CTSLA%2CMETA

DB_PATH = "data/nfl_odds.duckdb"
DB_URL = "https://github.com/bobby-king3/nfl-market-movement-tracker/releases/download/v1.0.0/nfl_odds.duckdb"

if not os.path.exists(DB_PATH):
    os.makedirs("data", exist_ok=True)
    with st.spinner("Downloading database..."):
        urllib.request.urlretrieve(DB_URL, DB_PATH)

st.set_page_config(
    page_title="NFL Market Movement Tracker",
    page_icon=":football:",
    layout="wide",
)

"""
# NFL Market Movement Tracker

Track how market lines move across operators leading up to kickoff.
"""

""

OPERATOR_DISPLAY = {
    "ballybet": "Bally Bet",
    "betmgm": "BetMGM",
    "betrivers": "BetRivers",
    "draftkings": "DraftKings",
    "espnbet": "ESPN BET/theScore",
    "fanatics": "Fanatics",
    "fanduel": "FanDuel",
    "fliff": "Fliff",
    "hardrockbet": "Hard Rock Bet",
    "pinnacle": "Pinnacle",
    "williamhill_us": "Caesars",
}

OPERATOR_COLORS = {
    "pinnacle": "#CC0000",
    "draftkings": "#53A548",
    "fanduel": "#095190",
    "betmgm": "#C4A137",
    "hardrockbet": "#7D1783",
    "betrivers": "#FFD700",
    "fanatics": "#A1B8E9",
    "espnbet": "#FF3E3E",
    "williamhill_us": "#1B3C6B",
    "ballybet": "#E63946",
    "fliff": "#FF69B4",
}

DEFAULT_OPERATORS = ["pinnacle", "draftkings", "fanduel", "hardrockbet", "betrivers"]


WEEK_LABELS = {
    **{i: f"Week {i}" for i in range(1, 19)},
    19: "Wild Card",
    20: "Divisional",
    21: "Conference Championships",
    22: "Super Bowl",
}

@st.cache_data
def get_games():
    conn = duckdb.connect(DB_PATH, read_only=True)
    games = conn.execute("""
        select event_id, home_team, away_team,
               max(game_start_time) as game_start_time,
               max(nfl_week) as nfl_week
        from fct_line_movements
        group by event_id, home_team, away_team
        order by game_start_time desc
    """).fetchall()
    conn.close()
    return games

@st.cache_data
def get_line_movements(event_id, sportsbooks, market_type):
    conn = duckdb.connect(DB_PATH, read_only=True)
    placeholders = ",".join(["?" for _ in sportsbooks])
    df = conn.execute(f"""
        select captured_at, sportsbook, line, price, outcome, implied_prob
        from fct_line_movements
        where event_id = ?
          and sportsbook in ({placeholders})
          and market_type = ?
        order by captured_at
    """, [event_id] + sportsbooks + [market_type]).fetchdf()
    conn.close()
    return df

@st.cache_data
def get_game_summary(event_id, sportsbooks, market_type):
    conn = duckdb.connect(DB_PATH, read_only=True)
    placeholders = ",".join(["?" for _ in sportsbooks])
    df = conn.execute(f"""
        select sportsbook, outcome, opening_line, closing_line, total_line_movement,
               opening_price, closing_price, opening_implied_prob_pct,
               closing_implied_prob_pct, implied_prob_pct_change, capture_count
        from fct_game_summary
        where event_id = ?
          and sportsbook in ({placeholders})
          and market_type = ?
        order by sportsbook, outcome
    """, [event_id] + sportsbooks + [market_type]).fetchdf()
    conn.close()
    return df

top_cols = st.columns([1, 3])

games = get_games()

games_with_weeks = []
for g in games:
    event_id, home, away, start_time, week_num = g
    week_label = WEEK_LABELS.get(week_num, f"Week {week_num}")
    game_label = f"{home} vs {away} — {start_time.strftime('%b %d')}"
    games_with_weeks.append((event_id, home, away, start_time, week_num, week_label, game_label))

all_teams = sorted(set(
    team for g in games_with_weeks for team in (g[1], g[2])
))

filter_cell = top_cols[0].container(border=True)

with filter_cell:
    browse_mode = st.pills("Browse by", ["Week", "Team"], default="Week")

    if browse_mode == "Week":
        # Get available weeks in order
        available_weeks = sorted(set(g[4] for g in games_with_weeks))
        week_options = [WEEK_LABELS.get(w, f"Week {w}") for w in available_weeks]

        selected_week_label = st.selectbox("Week", week_options, index=len(week_options) - 1)
        selected_week_num = available_weeks[week_options.index(selected_week_label)]

        # Filter games to selected week, sorted by game date
        week_games = sorted(
            [g for g in games_with_weeks if g[4] == selected_week_num],
            key=lambda g: g[3],
        )
        game_options = {g[6]: g[0] for g in week_games}

    else:
        selected_team = st.selectbox("Team", all_teams)

        # Filter games involving selected team, most recent first
        team_games = sorted(
            [g for g in games_with_weeks if selected_team in (g[1], g[2])],
            key=lambda g: g[3],
            reverse=True,
        )
        game_options = {f"{g[5]}: {g[6]}": g[0] for g in team_games}

    selected_game_label = st.selectbox("Game", list(game_options.keys()))
    selected_event_id = game_options[selected_game_label]

    selected_operators = st.multiselect(
        "Operators",
        options=list(OPERATOR_DISPLAY.keys()),
        default=DEFAULT_OPERATORS,
        format_func=lambda x: OPERATOR_DISPLAY.get(x, x),
    )

    market_type = st.pills(
        "Market",
        ["h2h", "spreads", "totals"],
        default="h2h",
        format_func=lambda x: {"h2h": "Head to Head", "spreads": "Spread", "totals": "Total"}[x],
    )

if not selected_operators:
    filter_cell.info("Select at least one operator.", icon=":material/info:")
    st.stop()

movements = get_line_movements(selected_event_id, selected_operators, market_type)
summary = get_game_summary(selected_event_id, selected_operators, market_type)

if movements.empty:
    filter_cell.info("No data for this selection.", icon=":material/info:")
    st.stop()

outcomes = movements["outcome"].unique().tolist()

if market_type == "spreads":
    home_outcomes = [o for o in outcomes if movements[movements["outcome"] == o]["line"].iloc[0] < 0]
    selected_outcome = home_outcomes[0] if home_outcomes else outcomes[0]
elif market_type == "h2h":
    latest_probs = movements.sort_values("captured_at").groupby("outcome")["implied_prob"].last()
    selected_outcome = latest_probs.idxmax() if not latest_probs.empty else outcomes[0]
else:
    selected_outcome = "Over" if "Over" in outcomes else outcomes[0]

with filter_cell:
    selected_outcome = st.pills("Outcome", outcomes, default=selected_outcome)

filtered = movements[movements["outcome"] == selected_outcome]
outcome_summary = summary[summary["outcome"] == selected_outcome]

other_outcome = [o for o in outcomes if o != selected_outcome]
if other_outcome:
    other_filtered = movements[movements["outcome"] == other_outcome[0]][["captured_at", "sportsbook", "price"]].rename(
        columns={"price": "other_price"}
    )
    filtered = filtered.merge(other_filtered, on=["captured_at", "sportsbook"], how="left")

chart_cell = top_cols[1].container(border=True)

hover_data = {"price": True}
if "other_price" in filtered.columns:
    hover_data["other_price"] = True

with chart_cell:
    chart_data = filtered.copy()
    chart_data["operator"] = chart_data["sportsbook"].map(OPERATOR_DISPLAY)
    display_color_map = {OPERATOR_DISPLAY[k]: v for k, v in OPERATOR_COLORS.items() if k in OPERATOR_COLORS}

    if market_type == "h2h":
        y_col = "price"
        y_label = "Head to Head Price"
    else:
        y_col = "line"
        y_label = "Line"

    fig_line = px.line(
        chart_data,
        x="captured_at",
        y=y_col,
        color="operator",
        labels={
            "captured_at": "Date",
            y_col: y_label,
            "operator": "Operator",
            "price": f"{selected_outcome} Price",
            "other_price": f"{other_outcome[0]} Price" if other_outcome else "Price",
        },
        line_shape="hv",
        hover_data=hover_data,
        color_discrete_map=display_color_map,
    )
    if market_type == "h2h":
        price_min = filtered["price"].min() - 5
        price_max = filtered["price"].max() + 5
        fig_line.update_yaxes(range=[price_min, price_max])
    else:
        line_min = filtered["line"].min() - 1
        line_max = filtered["line"].max() + 1
        fig_line.update_yaxes(range=[line_min, line_max], dtick=0.5)
    fig_line.update_traces(line=dict(width=2.5))
    fig_line.update_layout(
        hovermode="x unified",
        height=450,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    if market_type == "spreads":
        chart_label = f"Spread — {selected_outcome}"
    elif market_type == "h2h":
        chart_label = f"Head to Head — {selected_outcome}"
    else:
        chart_label = f"Total — {selected_outcome}"
    st.caption(chart_label)
    st.plotly_chart(fig_line, use_container_width=True)

# Use Pinnacle as consensus data point
if not outcome_summary.empty:
    pinnacle_row = outcome_summary[outcome_summary["sportsbook"] == "pinnacle"]
    metric_row = pinnacle_row.iloc[0] if not pinnacle_row.empty else outcome_summary.iloc[0]

    line_movement = metric_row["total_line_movement"]
    prob_change = metric_row["implied_prob_pct_change"] * 100

    with top_cols[0].container(border=True):
        m1, m2 = st.columns(2)
        if market_type == "h2h":
            m1.metric("Win Probability", f"{metric_row['closing_implied_prob_pct'] * 100:.1f}%",
                      delta=f"{prob_change:+.1f}%" if round(prob_change, 2) != 0 else None,
                      delta_color="normal")
        else:
            m1.metric("Line", metric_row["closing_line"],
                      delta=f"{line_movement:+.1f}" if line_movement != 0 else None,
                      delta_color="normal")
        m2.metric("Price", int(metric_row["closing_price"]),
                  delta=f"{prob_change:+.1f}%" if round(prob_change, 2) != 0 else None,
                  delta_color="normal")
        st.caption("Pinnacle closing odds")

if not summary.empty:
    """
    ## Closing Implied Probability by Operator
    """

    # Pivot to get both outcomes side by side per sportsbook
    prob_data = summary.copy()
    prob_data["closing_pct"] = prob_data["closing_implied_prob_pct"] * 100
    prob_data["display_name"] = prob_data["sportsbook"].map(OPERATOR_DISPLAY)

    other_name = other_outcome[0] if other_outcome else None

    if other_name:
        side_selected = prob_data[prob_data["outcome"] == selected_outcome].set_index("sportsbook")
        side_other = prob_data[prob_data["outcome"] == other_name].set_index("sportsbook")

        books = [s for s in selected_operators if s in side_selected.index and s in side_other.index]
        display_names = [OPERATOR_DISPLAY.get(b, b) for b in books]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=display_names,
            x=[side_other.loc[b, "closing_pct"] for b in books],
            name=other_name,
            orientation="h",
            marker_color="#5B8FC9",
            text=[f"{side_other.loc[b, 'closing_pct']:.1f}%" for b in books],
            textposition="inside",
            hovertemplate="%{y}: %{x:.1f}%<extra>" + other_name + "</extra>",
        ))

        fig.add_trace(go.Bar(
            y=display_names,
            x=[side_selected.loc[b, "closing_pct"] for b in books],
            name=selected_outcome,
            orientation="h",
            marker_color="#8B5E8B",
            text=[f"{side_selected.loc[b, 'closing_pct']:.1f}%" for b in books],
            textposition="inside",
            hovertemplate="%{y}: %{x:.1f}%<extra>" + selected_outcome + "</extra>",
        ))

        # Add margin annotations at end of each bar
        for j, b in enumerate(books):
            total = side_selected.loc[b, "closing_pct"] + side_other.loc[b, "closing_pct"]
            margin = total - 100
            fig.add_annotation(
                x=total,
                y=display_names[j],
                text=f"  {margin:.1f}% margin",
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color="#999"),
            )

        fig.add_vline(x=50, line_dash="dash", line_color="white", line_width=1, opacity=0.5)

        max_total = max(
            side_selected.loc[b, "closing_pct"] + side_other.loc[b, "closing_pct"]
            for b in books
        )

        fig.update_layout(
            barmode="stack",
            height=45 * len(books) + 80,
            margin=dict(l=10, r=80, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, traceorder="normal"),
            xaxis_title="Implied Probability %",
            yaxis_title="",
            xaxis=dict(range=[0, max_total + 12]),
        )

        st.plotly_chart(fig, use_container_width=True)

""
""

if not outcome_summary.empty and market_type != "h2h":
    """
    ## Opening vs Closing Line
    """

    dumbbell_data = outcome_summary.copy()
    dumbbell_data["display_name"] = dumbbell_data["sportsbook"].map(OPERATOR_DISPLAY)
    display_names = dumbbell_data["display_name"].tolist()

    fig_db = go.Figure()

    moved = dumbbell_data[dumbbell_data["total_line_movement"] != 0]
    no_move = dumbbell_data[dumbbell_data["total_line_movement"] == 0]

    # Connecting lines for moved sportsbooks
    for _, row in moved.iterrows():
        book_color = OPERATOR_COLORS.get(row["sportsbook"], "#888")
        fig_db.add_trace(go.Scatter(
            x=[row["opening_line"], row["closing_line"]],
            y=[row["display_name"], row["display_name"]],
            mode="lines",
            line=dict(color=book_color, width=3),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Opening dots (only for moved lines)
    if not moved.empty:
        fig_db.add_trace(go.Scatter(
            x=moved["opening_line"],
            y=moved["display_name"],
            mode="markers",
            showlegend=False,
            marker=dict(size=12, color="white", line=dict(width=2, color="#666")),
            hovertemplate="%{y}<br>Opening: %{x}<extra></extra>",
        ))

    # Closing dots (only for moved lines)
    if not moved.empty:
        fig_db.add_trace(go.Scatter(
            x=moved["closing_line"],
            y=moved["display_name"],
            mode="markers",
            showlegend=False,
            marker=dict(
                size=12,
                color=[OPERATOR_COLORS.get(s, "#888") for s in moved["sportsbook"]],
                line=dict(width=2, color="white"),
            ),
            hovertemplate="%{y}<br>Closing: %{x}<extra></extra>",
        ))

    # No-movement dots — single filled dot
    if not no_move.empty:
        fig_db.add_trace(go.Scatter(
            x=no_move["closing_line"],
            y=no_move["display_name"],
            mode="markers",
            showlegend=False,
            marker=dict(
                size=12,
                color=[OPERATOR_COLORS.get(s, "#888") for s in no_move["sportsbook"]],
                line=dict(width=2, color="white"),
                symbol="diamond",
            ),
            hovertemplate="%{y}<br>Line: %{x} (no change)<extra></extra>",
        ))

    # Movement annotations
    for _, row in moved.iterrows():
        movement = row["total_line_movement"]
        fig_db.add_annotation(
            x=max(row["opening_line"], row["closing_line"]),
            y=row["display_name"],
            text=f"  {movement:+.1f}",
            showarrow=False,
            xanchor="left",
            font=dict(size=11, color="#999"),
        )

    all_lines = list(dumbbell_data["opening_line"]) + list(dumbbell_data["closing_line"])
    line_min_db = min(all_lines) - 1
    line_max_db = max(all_lines) + 1.5

    fig_db.update_layout(
        height=45 * len(dumbbell_data) + 80,
        margin=dict(l=10, r=10, t=10, b=40),
        xaxis_title="Line",
        yaxis_title="",
        xaxis=dict(range=[line_min_db, line_max_db], dtick=0.5),
        showlegend=False,
    )

    st.plotly_chart(fig_db, use_container_width=True)
    st.caption("White circle = opening line, colored circle = closing line, diamond = no movement.")

""
""

if not filtered.empty:
    """
    ## Odds Pricing Heatmap
    """

    heat_data = filtered[["captured_at", "sportsbook", "price"]].copy()
    heat_data["display_name"] = heat_data["sportsbook"].map(OPERATOR_DISPLAY)

    # Pivot: sportsbooks as rows, capture times as columns
    pivot = heat_data.pivot_table(index="sportsbook", columns="captured_at", values="price", aggfunc="first")
    # Maintain selected sportsbook order
    ordered_books = [s for s in selected_operators if s in pivot.index]
    pivot = pivot.loc[ordered_books]
    display_names = [OPERATOR_DISPLAY.get(b, b) for b in ordered_books]

    max_cols = 20
    if len(pivot.columns) > max_cols:
        step = len(pivot.columns) // max_cols
        pivot = pivot.iloc[:, ::step]

    time_labels = [t.strftime("%b %d %Hh") for t in pivot.columns]

    price_min = pivot.min().min()
    price_max = pivot.max().max()

    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=time_labels,
        y=display_names,
        colorscale=[[0, "#1a2a4a"], [0.5, "#4A90D9"], [1, "#FF4444"]],
        text=[[f"{int(v)}" if not pd.isna(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=12),
        hovertemplate="<b>%{y}</b><br>%{x}<br>Price: %{z}<extra></extra>",
        colorbar=dict(title="Price"),
        zmin=price_min,
        zmax=price_max,
    ))

    fig_heat.update_layout(
        height=55 * len(ordered_books) + 80,
        margin=dict(l=10, r=10, t=10, b=40),
        xaxis_title="",
        yaxis_title="",
    )

    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption(f"Showing {selected_outcome} — color intensity reflects how aggressively each operator is pricing this outcome.")

""
""

if not filtered.empty:
    """
    ## Implied Probability Over Time
    """

    prob_over_time = filtered[["captured_at", "sportsbook", "implied_prob"]].copy()
    prob_over_time["implied_prob"] = prob_over_time["implied_prob"] * 100
    prob_over_time["display_name"] = prob_over_time["sportsbook"].map(OPERATOR_DISPLAY)

    fig_prob = go.Figure()

    prob_min = prob_over_time["implied_prob"].min()
    prob_max = prob_over_time["implied_prob"].max()

    for book in selected_operators:
        book_data = prob_over_time[prob_over_time["sportsbook"] == book]
        if book_data.empty:
            continue
        color = OPERATOR_COLORS.get(book, "#888888")
        fig_prob.add_trace(go.Scatter(
            x=book_data["captured_at"],
            y=book_data["implied_prob"],
            name=OPERATOR_DISPLAY.get(book, book),
            mode="lines",
            line=dict(width=2.5, color=color),
            hovertemplate="%{y:.1f}%<extra>" + OPERATOR_DISPLAY.get(book, book) + "</extra>",
        ))

    y_padding = max((prob_max - prob_min) * 0.3, 1)
    fig_prob.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="Implied Probability %",
        yaxis=dict(
            range=[prob_min - y_padding, prob_max + y_padding],
            ticksuffix="%",
        ),
        xaxis_title="",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig_prob, use_container_width=True)
    st.caption(f"Market confidence for {selected_outcome} over time, derived from odds pricing.")

""
""

"""
## Game Summary
"""

if market_type == "h2h":
    summary_display = summary[["sportsbook", "outcome", "opening_price", "closing_price",
                                "opening_implied_prob_pct", "closing_implied_prob_pct",
                                "implied_prob_pct_change"]].copy()
    summary_display["opening_implied_prob_pct"] = (summary_display["opening_implied_prob_pct"] * 100).round(1)
    summary_display["closing_implied_prob_pct"] = (summary_display["closing_implied_prob_pct"] * 100).round(1)
    summary_display["implied_prob_pct_change"] = (summary_display["implied_prob_pct_change"] * 100).round(1)
    summary_display["sportsbook"] = summary_display["sportsbook"].map(OPERATOR_DISPLAY)
    summary_display = summary_display.rename(columns={
        "sportsbook": "Operator",
        "outcome": "Outcome",
        "opening_price": "Opening Price",
        "closing_price": "Closing Price",
        "opening_implied_prob_pct": "Opening Win %",
        "closing_implied_prob_pct": "Closing Win %",
        "implied_prob_pct_change": "Win % Change",
    })
else:
    summary_display = summary[["sportsbook", "outcome", "opening_line", "closing_line",
                                "total_line_movement", "opening_price", "closing_price"]].copy()
    summary_display["sportsbook"] = summary_display["sportsbook"].map(OPERATOR_DISPLAY)
    summary_display = summary_display.rename(columns={
        "sportsbook": "Operator",
        "outcome": "Outcome",
        "opening_line": "Opening Line",
        "closing_line": "Closing Line",
        "total_line_movement": "Line Movement",
        "opening_price": "Opening Price",
        "closing_price": "Closing Price",
    })
st.dataframe(summary_display, use_container_width=True, hide_index=True)
