import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import graphviz

# Database connection details
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="cricket_dataset_practice"
)

@st.cache_data
def load_data(query, params=None): # Add params argument
    if params is None:
        df = pd.read_sql(query, mydb)
    else:
        df = pd.read_sql(query, mydb, params=params) # Pass params to pd.read_sql
    return df

st.set_page_config(layout="wide")


st.sidebar.title("Cricket Data Insights and Analysis")
st.title("Cricket Analytics Dashboard")
st.write("Explore cricket statistics and insights.")

# Sidebar for Filters
st.sidebar.header("Filters")
match_type = st.sidebar.selectbox("Match Type", ["All", "Test", "ODI", "T20"])
team = st.sidebar.selectbox("Team", ["All"] + list(load_data("SELECT DISTINCT team1 FROM match_details UNION SELECT DISTINCT team2 FROM match_details")['team1'].sort_values().unique()))

# ---  Visualizations ---

col1, col2, col3 = st.columns((1.5, 4.5, 2))

with col1:

    # 1. Top 10 Batsmen by Runs (All Formats or Selected)
    #st.subheader("Top 10 Batsmen by Runs")
    query_batsmen_runs = f"""
        SELECT r.person_name, SUM(d.runs_batter) AS total_runs
        FROM deliveries d
        JOIN registry r ON d.batter = r.person_id
        JOIN match_details md ON d.match_id = md.match_id
        { "WHERE md.match_type = '"+match_type+"'" if match_type != "All" else ""}
        { "AND (md.team1 = '"+team+"' OR md.team2 = '"+team+"')" if team != "All" else ""}
        GROUP BY r.person_name
        ORDER BY total_runs DESC
        LIMIT 10;
    """
    df_batsmen_runs = load_data(query_batsmen_runs)
    fig_batsmen_runs = px.bar(df_batsmen_runs, x="person_name", y="total_runs",title="Top 10 Batsmen by Runs",color_discrete_sequence=px.colors.qualitative.Prism)

    st.plotly_chart(fig_batsmen_runs)


    # 2. Total Centuries (All Formats or Selected)
    #st.subheader("Total Centuries")
    params = {}
    conditions = []

    if match_type != "All":
        conditions.append("md.match_type = %(match_type)s")  # Use %()s placeholder
        params["match_type"] = match_type

    if team != "All":
        conditions.append("(md.team1 = %(team)s OR md.team2 = %(team)s)") # Use %()s placeholder
        params["team"] = team

    query_match_ids = "SELECT match_id FROM match_details md"
    if conditions:
        query_match_ids += " WHERE " + " AND ".join(conditions)

    query_centuries = f"""
        SELECT r.person_name, SUM(CASE WHEN runs >= 100 THEN FLOOR(runs / 100) ELSE 0 END) AS total_centuries
        FROM (
            SELECT d.match_ID, d.innings, d.batter, SUM(d.runs_batter) AS runs
            FROM deliveries d
            WHERE d.match_ID IN ({query_match_ids})
            GROUP BY d.match_ID, d.innings, d.batter
        ) AS innings_runs
        JOIN registry r ON innings_runs.batter = r.person_id
        GROUP BY r.person_name
        ORDER BY total_centuries DESC
        LIMIT 20;
    """

    df_centuries = load_data(query_centuries, params) # Pass parameters
    fig_centuries = px.bar(df_centuries, x="person_name", y="total_centuries", title="Total Centuries")
    st.plotly_chart(fig_centuries)

    st.subheader("Top 10 Batsmen by Average")
    query_batsmen_avg = f"""
        SELECT r.person_name, AVG(d.runs_batter) AS batting_avg
        FROM deliveries d
        JOIN registry r ON d.batter = r.person_id
        JOIN match_details md ON d.match_id = md.match_id
        WHERE md.match_type = '{match_type}' { "AND (md.team1 = '"+team+"' OR md.team2 = '"+team+"')" if team != "All" else ""}
        GROUP BY r.person_name
        ORDER BY batting_avg DESC
        LIMIT 10;
    """
    df_batsmen_avg = load_data(query_batsmen_avg)
    fig_batsmen_avg = px.bar(df_batsmen_avg, x="person_name", y="batting_avg", title="Batting Average")
    st.plotly_chart(fig_batsmen_avg)

    st.subheader("Most Runs in a Single Inning")
    query_highest_score = f"""
        SELECT r.person_name, d.runs_batter, md.match_id, md.team1, md.team2
        FROM deliveries d
        JOIN registry r ON d.batter = r.person_id
        JOIN match_details md ON d.match_id = md.match_id
        WHERE md.match_type = '{match_type}' { "AND (md.team1 = '"+team+"' OR md.team2 = '"+team+"')" if team != "All" else ""}
        ORDER BY d.runs_batter DESC
        LIMIT 10;
    """
    df_highest_score = load_data(query_highest_score)
    st.bar_chart(df_highest_score.set_index("person_name")["runs_batter"])  # Streamlit bar chart

with col2:  # Bowling & Match Dynamics
    st.subheader("Narrowest Margin of Victory")

    query_narrowest = f"""
        SELECT md.match_id, md.team1, md.team2, md.winner, md.outcome_type, 
               CAST(md.outcome_value AS UNSIGNED) AS margin_value  -- Directly cast if runs/wickets
        FROM match_details md
        WHERE md.outcome_type IN ('runs', 'wickets')  -- Filter AFTER casting
          { "AND md.match_type = '"+match_type+"'" if match_type != "All" else ""}
          { "AND (md.team1 = '"+team+"' OR md.team2 = '"+team+"')" if team != "All" else ""}
        ORDER BY margin_value ASC
        LIMIT 10;
    """

    df_narrowest = load_data(query_narrowest)

    if not df_narrowest.empty:
        st.dataframe(df_narrowest)
    else:
        st.write("No matches found with runs or wickets outcome type for the selection.")

    st.subheader("Impact of Toss")
    query_toss_impact = f"""
        SELECT toss_decision, (SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END) * 100.0) / COUNT(*) AS win_percentage
        FROM match_details
        WHERE match_type = %(match_type)s AND (team1 = %(team)s OR team2 = %(team)s)  -- Corrected and parameterized
        GROUP BY toss_decision
        ORDER BY win_percentage DESC;
    """

    params = {"match_type": match_type, "team": team}
    df_toss_impact = load_data(query_toss_impact, params)

    if not df_toss_impact.empty:
        fig_toss_impact = px.bar(df_toss_impact, x='toss_decision', y='win_percentage', title='Win Percentage by Toss Decision')
        st.plotly_chart(fig_toss_impact)
    else:
        st.write("No data found for the selection.")

    st.subheader("Player of the Match Awards (Pie Chart)")  # Changed title

    query_pom = f"""
        SELECT r.person_name, COUNT(*) AS pom_awards
        FROM match_details md
        JOIN registry r ON md.player_of_match = r.person_id
        WHERE { "md.match_type = '"+match_type+"' AND" if match_type != "All" else ""} (md.team1 = '{team}' OR md.team2 = '{team}')
        GROUP BY r.person_name
        ORDER BY pom_awards DESC
        LIMIT 10;
    """

    df_pom = load_data(query_pom)

    if not df_pom.empty:
        # Donut Chart (optional - just add hole=0.3)
        fig_pom_donut = px.pie(df_pom, values='pom_awards', names='person_name', title='Player of the Match Awards (Donut)', hole=0.3)
        st.plotly_chart(fig_pom_donut)

    else:
        st.write("No data found for the selection.")

with col3:
    # 2. Leading Wicket-Takers (All Formats or Selected)
    #st.subheader("Leading Wicket-Takers")
    query_wickets = f"""
        SELECT r.person_name, COUNT(d.player_out) AS total_wickets
        FROM deliveries d
        JOIN registry r ON d.bowler = r.person_id
        JOIN match_details md ON d.match_id = md.match_id
        WHERE d.dismissal_kind IS NOT NULL 
        { "AND md.match_type = '"+match_type+"'" if match_type != "All" else ""}
        { "AND (md.team1 = '"+team+"' OR md.team2 = '"+team+"')" if team != "All" else ""}
        GROUP BY r.person_name
        ORDER BY total_wickets DESC
        LIMIT 10;
    """
    df_wickets = load_data(query_wickets)
    fig_wickets = px.bar(df_wickets, x="person_name", y="total_wickets",title="Leading Wicket-Takers")
    st.plotly_chart(fig_wickets)

    # 2.  Most Wickets in a Single Match
    #st.subheader("Most Wickets in a Single Match")
    query_most_wickets_match = f"""
        SELECT r.person_name, COUNT(d.player_out) AS wickets_in_match, md.match_id, md.team1, md.team2
        FROM deliveries d
        JOIN registry r ON d.bowler = r.person_id
        JOIN match_details md ON d.match_id = md.match_id
        WHERE d.dismissal_kind IS NOT NULL
        GROUP BY r.person_name, md.match_id, md.team1, md.team2
        ORDER BY wickets_in_match DESC
        LIMIT 10;
    """
    df_most_wickets_match = load_data(query_most_wickets_match)
    fig_most_wickets_match = px.bar(df_most_wickets_match, x="person_name", y="wickets_in_match", title="Most Wickets in a Single Match")
    st.plotly_chart(fig_most_wickets_match)

    for mt in ["Test", "ODI", "T20"]:
        st.subheader(f"Team Win Percentage ({mt})")
        query_win_percent = f"""
            SELECT team, match_type, (SUM(CASE WHEN winner = team THEN 1 ELSE 0 END) * 100.0) / COUNT(*) AS win_percentage
            FROM (
                SELECT team1 AS team, winner, '{mt}' as match_type  -- Include match_type as a literal
                FROM match_details
                WHERE match_type = '{mt}' { "AND (team1 = '"+team+"' OR team2 = '"+team+"')" if team != "All" else ""}
                UNION ALL
                SELECT team2 AS team, winner, '{mt}' as match_type  -- Include match_type as a literal
                FROM match_details
                WHERE match_type = '{mt}' { "AND (team1 = '"+team+"' OR team2 = '"+team+"')" if team != "All" else ""}
            ) AS all_teams
            GROUP BY team, match_type
            ORDER BY win_percentage DESC;
        """
        df_win_percent = load_data(query_win_percent)

        if not df_win_percent.empty:
            # No need to melt if match_type is already in the DataFrame

            fig_win_percent = px.bar(
                df_win_percent,  # Use the original DataFrame
                x='team',
                y='win_percentage',
                color='match_type',  # Now 'match_type' is a valid column
                title=f'Win Percentage ({mt})'
            )

            st.plotly_chart(fig_win_percent)
        else:
            st.write(f"No data found for {mt} matches with the selected criteria.")
 
