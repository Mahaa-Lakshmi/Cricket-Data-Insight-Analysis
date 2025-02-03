import streamlit as st
import mysql.connector as db
import pandas as pd
import plotly.express as px
import re
import plotly.figure_factory as ff


dbm=db.connect(
            host="localhost",
    user="root",
    password="root",
    database="cricket_dataset_practice"
        )
st.set_page_config(layout="wide")

st.session_state.active_Tab=None


@st.cache_data
def load_data(query, params=None): # Add params argument
    if params is None:
        df = pd.read_sql(query, dbm)
    else:
        df = pd.read_sql(query, dbm, params=params) # Pass params to pd.read_sql
    return df

def process_season(season):
    if isinstance(season, (int, float)):  # Handle cases where season might already be a number
        return str(int(season)) # Convert to string and return
    if isinstance(season, str):
        match = re.match(r'(\d{4})/(\d{2})', season)  # Check for yyyy/yy format
        if match:
            year1 = int(match.group(1))
            return year1  # Return the first year for sorting
        else:
            try:
                year = int(season)  # Try converting to integer (yyyy format)
                return year
            except ValueError:
                return None # Or handle as you see fit (e.g., return a special value, raise an exception)
    return None

st.title("Cricket Analytics Dashboard")
st.write("Explore cricket statistics and insights.")


# Sidebar for Filters
st.sidebar.header("Filters")
match_type = st.sidebar.selectbox("Match Type", ["All", "Test", "ODI", "T20"])
team = st.sidebar.selectbox("Team", ["All"] + list(load_data("SELECT DISTINCT team1 FROM match_details UNION SELECT DISTINCT team2 FROM match_details")['team1'].sort_values().unique()))


tab1, tab2, tab3, tab4, tab5 = st.tabs(["Player Performance", "Overall Match Details","Team Performance","Umpiring & Fielding","Historical Trends"])



with tab1:    
    gender=st.radio(
        "Choose gender of the player",
        ["Female", "Male"],
        index=1,horizontal=True)
    query=f"""select distinct r.person_name
            from players p
            join registry r on p.person_id=r.person_id
            join match_details md on md.match_id=p.match_ID
            where gender=%s
            order by r.person_name;"""
    player_list=load_data(query,(gender,))          
    player_name=st.selectbox("Choose a player name",player_list) 
    sub_col1,sub_col2,sub_col3,sub_col4=st.columns(4,vertical_alignment="bottom")
    with sub_col1:
        #st.write("will add")
        query=f"""
        SELECT r.person_name, sum(d.runs_batter) AS total_runs
        FROM deliveries d
        JOIN registry r ON d.batter = r.person_id
        JOIN match_details md ON d.match_id = md.match_id
        WHERE r.person_name = '{player_name}' { "AND (match_type = '"+match_type+"')" if match_type != "All" else ""}
        GROUP BY r.person_name
        ORDER BY total_runs DESC;
        """
        total_Runs=load_data(query).get("total_runs").iloc[0]
        st.metric(label="Total runs", value=int(total_Runs))

    with sub_col2:                
        query_batsmen_avg=f"""SELECT person_name, SUM(total_runs) AS total_runs, COUNT(DISMISS) AS dismissals,
            COUNT(CASE WHEN innings IN (1, 2, 3, 4) THEN 1 END) AS innings_played -- Count innings played
            FROM (
                SELECT d.match_id AS match_id, match_type AS match_type, r.person_name AS person_name, d.innings AS innings, d.runs_batter AS total_runs, d.dismissal_kind AS DISMISS
                FROM deliveries d
                JOIN registry r ON d.batter = r.person_id
                JOIN match_details md ON d.match_id = md.match_id
                WHERE r.person_name = '{player_name}' { "AND (match_type = '"+match_type+"')" if match_type != "All" else ""}
            ) AS essentials
            GROUP BY person_name;"""
        
        rows=load_data(query_batsmen_avg)
        #print(rows)
        person_name = rows.get("person_name").iloc[0]
        total_runs = rows.get("total_runs").iloc[0]
        dismissals = rows.get("dismissals").iloc[0]
        innings_played = rows.get("innings_played").iloc[0]

        if dismissals > 0:
            batting_average = total_runs / dismissals
            #print(f"Player: {person_name}, Overall Batting Average: {batting_average:.2f}")
            val=f"{batting_average:.2f}"
        else:
            if innings_played > 0:
              batting_average = total_runs
              #print(f"Player: {person_name}, Overall Batting Average: {batting_average:.2f}*") # * indicates not out
              val=f"{batting_average:.2f}"
            else:
                val= "0.00"
        st.metric(label="Batting Average", value=val)
        


    with sub_col3:                
        #st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta)
        #st.metric(label="Total Wickets", value="23.M", delta="first_state_delta")
        query=f"""
        SELECT COUNT(d.player_out) AS total_wickets
        FROM deliveries d
        JOIN registry r ON d.bowler = r.person_id  
        join match_details md on md.match_id=d.match_id
        WHERE r.person_name = '{player_name}' AND d.dismissal_kind IS NOT NULL { "AND (match_type = '"+match_type+"')" if match_type != "All" else ""};
        """
        
        total_wickets=load_data(query)
        total_wickets=total_wickets.get("total_wickets").iloc[0]
        #print(total_wickets)
        st.metric(label="Total Wickets taken", value=f"""{total_wickets}""")
    with sub_col4:                
        #st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta)
        query=f"""SELECT r.person_name,
           SUM(d.runs_total) AS total_runs_conceded,
           COUNT(DISTINCT CASE WHEN d.dismissal_kind IS NOT NULL AND d.bowler = r.person_id THEN d.id END) AS total_wickets,  -- Corrected wicket count
           CASE
               WHEN COUNT(DISTINCT CASE WHEN d.dismissal_kind IS NOT NULL AND d.bowler = r.person_id THEN d.id END) > 0 THEN  -- Avoid division by zero
                   CAST(SUM(d.runs_total) AS REAL) / COUNT(DISTINCT CASE WHEN d.dismissal_kind IS NOT NULL AND d.bowler = r.person_id THEN d.id END)
               ELSE
                   0  
           END AS bowling_average
            FROM deliveries d
            JOIN registry r ON d.bowler = r.person_id
            JOIN match_details md ON d.match_id = md.match_id
            WHERE r.person_name = '{player_name}' { "AND (match_type = '"+match_type+"')" if match_type != "All" else ""}
            GROUP BY r.person_name
            ORDER BY bowling_average;"""
        bowl_Avg=load_data(query)
        bowl_Avg=float(bowl_Avg.get("bowling_average").iloc[0])
        #print(bowl_Avg)
        st.metric(label="Bowling Average", value=f"""{bowl_Avg:.2f}""")

    col1, col2 = st.columns(2)
    with col1:
        query=f"""SELECT r.person_name,
               COUNT(DISTINCT CASE WHEN d.dismissal_kind IS NOT NULL AND d.bowler = r.person_id THEN d.id END) AS total_wickets,
               md.season  -- Use the season column
        FROM deliveries d
        JOIN registry r ON d.bowler = r.person_id
        JOIN match_details md ON d.match_id = md.match_id
        WHERE r.person_name = '{player_name}'
        { "AND md.match_type = '"+match_type+"'" if match_type != "All" else ""}
        GROUP BY r.person_name, md.season  -- Group by player and season;
"""
        top_wicket_takers=load_data(query)
        #print(top_wicket_takers)
        top_wicket_takers['processed_season'] = top_wicket_takers['season'].apply(process_season)
        #print(top_wicket_takers)
        fig = px.line(top_wicket_takers, x="processed_season", y="total_wickets", text="processed_season",title="Top Wickets by season")
        fig.update_traces(textposition="bottom right")
        st.plotly_chart(fig)

    with col2:
        
         query=f"""SELECT md.season, SUM(d.runs_batter) AS total_runs
                FROM deliveries d
                JOIN registry r ON d.batter = r.person_id
                JOIN match_details md ON d.match_id = md.match_id
                WHERE r.person_name = '{player_name}'
                { "AND md.match_type = '"+match_type+"'" if match_type != "All" else ""}
                GROUP BY md.season
                ORDER BY total_runs DESC;"""
         df_batsmen_runs = load_data(query)
         #print(df_batsmen_runs)
         df_batsmen_runs['processed_season'] = df_batsmen_runs['season'].apply(process_season)
         fig_batsmen_runs = px.bar(df_batsmen_runs, x="processed_season", y="total_runs",title="Total Runs by Season",color_discrete_sequence=px.colors.qualitative.Set1)
         st.plotly_chart(fig_batsmen_runs)

with tab2:
    active_Tab="tab2"
    st.session_state.active_Tab="tab2"
    if st.session_state.active_Tab==active_Tab:
        st.write("Tab 2")
    



