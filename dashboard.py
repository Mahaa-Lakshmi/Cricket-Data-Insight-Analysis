import streamlit as st
import mysql.connector as db
import pandas as pd
import plotly.express as px
import re
import plotly.figure_factory as ff
import urllib
from pathlib import Path
from zipfile import ZipFile
import requests




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

# Load the world cities data (only do this ONCE - use caching)
#@st.cache_data  # Cache the data loading
def load_world_cities_data():
    url = "https://simplemaps.com/static/data/world-cities/basic/simplemaps_worldcities_basicv1.74.zip"
    f = Path.cwd().joinpath(f'{urllib.parse.urlparse(url).path.split("/")[-1]}.zip')
    if not f.exists():
        r = requests.get(url, stream=True, headers={"User-Agent": "cricket_app"})
        with open(f, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    zfile = ZipFile(f)
    dfs = {f.filename: pd.read_csv(zfile.open(f)) for f in zfile.infolist() if f.filename.split(".")[1]=="csv"}
    return dfs["worldcities.csv"]  # Return the world cities DataFrame

# Load the data
world_cities_df = load_world_cities_data()

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


tab1, tab2, tab3, tab4 = st.tabs(["Player Performance", "Overall Match Details","Team Performance","Umpiring & Fielding"])



with tab1:    
    gender=st.radio(
        "Choose gender of the player",
        ["Female", "Male"],
        index=1,horizontal=True)
    query=f"""select distinct r.person_name
            from players p
            join registry r on p.person_id=r.person_id
            join match_details md on md.match_id=p.match_ID
            where gender=%s { "AND (p.team_name = '"+team+"')" if team != "All" else ""}
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
        total_Runs=load_data(query)
        if not total_Runs.empty:
            total_Runs=total_Runs.get("total_runs").iloc[0]
        else:
            total_Runs=0
        st.metric(label="Total runs", value=int(total_Runs), border=True)

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
        if not rows.empty:
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
        else:
            val = "0.00"
        st.metric(label="Batting Average", value=val, border=True)
        


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
        if not total_wickets.empty:
            total_wickets=total_wickets.get("total_wickets").iloc[0]
        #print(total_wickets)
        else:
            total_wickets=0
        st.metric(label="Total Wickets taken", value=f"""{total_wickets}""", border=True)
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
        #print(bowl_Avg)
        if not bowl_Avg.empty:
            bowl_Avg=float(bowl_Avg.get("bowling_average").iloc[0])
        else:
            bowl_Avg=0.00
        
        st.metric(label="Bowling Average", value=f"""{bowl_Avg:.2f}""", border=True)

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
    col1, col2 = st.columns(2)
    with col1:
        query=f"""SELECT team,
           SUM(CASE WHEN winner = team THEN 1 ELSE 0 END) AS wins,
           SUM(CASE WHEN winner != team AND winner IS NOT NULL THEN 1 ELSE 0 END) AS losses  -- Calculate losses
            FROM (
                SELECT team1 AS team, match_type, winner
                FROM match_details
                UNION ALL
                SELECT team2 AS team, match_type, winner
                FROM match_details
            ) AS all_teams
            WHERE 1=1 
            { "AND match_type = '"+match_type+"'" if match_type != "All" else ""} 
            { "AND team = '"+team+"'" if team != "All" else ""}
            GROUP BY team
            ORDER BY wins DESC;"""
        df = load_data(query)
        if not df.empty:
            #print(df)
            df['total_matches'] = df['wins'] + df['losses']

            # Calculate win and loss percentages for labels
            df['win_percentage'] = (df['wins'] / df['total_matches']) * 100
            df['loss_percentage'] = (df['losses'] / df['total_matches']) * 100

            #print(df)
            if len(df.index)>1:
                fig = px.scatter(df, y="win_percentage", x="loss_percentage",
                size="wins", color="team",
                    hover_name="team", log_x=True, size_max=60,title="Win/Loss Ratio")
                st.plotly_chart(fig)
            else:
                pie_data = pd.DataFrame({'Result': ['Wins', 'Losses'], 'Count': [df['wins'].iloc[0], df['losses'].iloc[0]]}) # Added iloc[0] to get the values

                fig_pom_donut = px.pie(
                    pie_data,
                    values='Count',  # Use counts (wins, losses)
                    names='Result',  # Labels for wins and losses
                    title=f"Win/Loss Ratio for {df['team'].iloc[0]}",  # Dynamic title
                    hole=0.7,
                    color='Result' # Set colors
                )
                st.plotly_chart(fig_pom_donut)

        else:
            st.write("No match data available.")

#bubble chart

        query=f"""SELECT venue,city,
SUM(CASE WHEN outcome_type is not null THEN 1 ELSE 0 END) as total_matches,
       (SUM(CASE WHEN outcome_type in ("runs","wickets") THEN 1 ELSE 0 END) * 100.0) / COUNT(*) AS win_percentage
FROM match_details
where 1=1
{ "AND match_type = '"+match_type+"'" if match_type != "All" else ""} 
{ "AND (team1 = '"+team+"' or team2='"+team+"') and winner='"+team+"' " if team != "All" else ""}
GROUP BY venue,city;"""
        df = load_data(query)
        #print(df)
        if not df.empty:
            # 1. Get the unique cities from your 'df'
            unique_cities = df['city'].unique()

            # 2. Filter the world cities data to include only the cities in 'df'
            filtered_world_cities = world_cities_df[world_cities_df['city'].isin(unique_cities)]

            # 3. Merge (now with the filtered world cities data)
            merged_df = pd.merge(df, filtered_world_cities, on='city', how='left')

            # Handle missing coordinates (if any)
            merged_df = merged_df.dropna(subset=['lat', 'lng'])
            #print(merged_df.columns)
            
            fig = px.scatter_map(merged_df,
                        lat="lat",
                        lon="lng",
                        hover_name="city", color="win_percentage",
                        size="total_matches",color_continuous_scale=px.colors.cyclical.IceFire,
                        zoom=1,title="Win Percentage based on Location")
            
    

            st.plotly_chart(fig)
        else:
            st.write("No data to show")

    with col2:
        
        query=f"""SELECT team,toss_decision,
       (SUM(CASE WHEN winner = team THEN 1 ELSE 0 END) * 100.0) / COUNT(*) AS win_percentage
FROM (
    SELECT team1 AS team, match_type, winner,toss_decision,toss_winner as tw
    FROM match_details
    UNION ALL
    SELECT team2 AS team, match_type, winner,toss_decision,toss_winner as tw
    FROM match_details
) AS all_teams
WHERE team=tw 
{ "AND match_type = '"+match_type+"'" if match_type != "All" else ""} 
{ "AND team = '"+team+"'" if team != "All" else ""}
GROUP BY toss_decision,team
ORDER BY team;"""
        #print(query)
        df=load_data(query)
        #print(df)
        if not df.empty:
            fig = px.bar(df, x='team', y='win_percentage', title='Field vs. Bat Performance', barmode='group',color="toss_decision")
            fig.update_layout(xaxis_title="team", yaxis_title="win_percentage") # Axis labels
            st.plotly_chart(fig)

        query=f"""select d.match_id,sum(d.runs_total) as total_runs_by_team,team1,team2,season,match_type
        FROM deliveries d
        JOIN match_details md ON d.match_id = md.match_id
        WHERE 1=1
        { "AND md.match_type = '"+match_type+"'" if match_type != "All" else ""} 
        { "AND (team1 = '"+team+"' or team2='"+team+"')" if team != "All" else ""}
        group by d.match_id;"""

        df=load_data(query)
        #print(df)
        if not df.empty:
            df['processed_season'] = df['season'].apply(process_season)
            #print(df)

            fig = px.area(df, x="processed_season", y="total_runs_by_team", color="match_type", line_group="match_type")
            #fig.update_traces(textposition="bottom right")
            st.plotly_chart(fig)

with tab3:    
    
    if team!="All":
        sub_col1,sub_col2,sub_col3,sub_col4=st.columns(4,vertical_alignment="bottom")
        query=f"""
            SELECT
               SUM(CASE WHEN winner = %s THEN 1 ELSE 0 END) AS wins,
               SUM(CASE WHEN winner != team1 and winner is not null and team1= %s THEN 1 ELSE 0 END) + SUM(CASE WHEN winner != team2 and winner is not null and team2= %s THEN 1 ELSE 0 END) AS losses,
               SUM(CASE WHEN winner IS NULL THEN 1 ELSE 0 END) AS ties,
               COUNT(*) AS total_matches  -- Total matches played
            FROM match_details
            WHERE { "(team1 = '"+team+"' or team2='"+team+"')" if team != "All" else ""}
            { "AND (match_type = '"+match_type+"')" if match_type != "All" else ""};
            """
        team_hist=load_data(query,(team,team,team,))
    
        
        if not team_hist.empty:
            with sub_col1:
                st.metric(label="Total matches", value=int(team_hist.get("total_matches").iloc[0]), border=True)

            with sub_col2:
                st.metric(label="Total wins", value=int(team_hist.get("wins").iloc[0]), border=True)  

            with sub_col3:
                st.metric(label="Total losses", value=int(team_hist.get("losses").iloc[0]), border=True)

            with sub_col4:   
                st.metric(label="Total ties", value=int(team_hist.get("ties").iloc[0]), border=True)
        else:
            pass           
            

        col1, col2 = st.columns(2)
        with col1:
            query_largest_victories = f"""
                SELECT winner, outcome_type, outcome_value, match_type, match_id,season
                FROM match_details
                WHERE (team1 = %s OR team2 = %s) AND winner = %s AND outcome_type IN ('runs')
                { "AND (match_type = '"+match_type+"')" if match_type != "All" else ""};
            """

            df_largest_victories = load_data(query_largest_victories, (team, team, team))  # Assuming 'team' is defined

            if not df_largest_victories.empty:
                # Convert outcome_value to numeric (it might be a string)
                df_largest_victories['outcome_value'] = pd.to_numeric(df_largest_victories['outcome_value'])
                # Sort by outcome_value descending
                df_largest_victories = df_largest_victories.sort_values('outcome_value', ascending=False)
                df_largest_victories['processed_season'] = df_largest_victories['season'].apply(process_season)               
                
                top_victories = df_largest_victories.head(10)
                top_victories['victory_description'] = top_victories.apply(
        lambda row: f"Won by {row['outcome_value']} {row['outcome_type']} ({row['processed_season']})", axis=1
    )
                        

                # Optional: Create a bar chart for visualization
                fig_largest_victories = px.bar(
                    top_victories,
                    x="outcome_value",
                    y="victory_description",
                    orientation='h',
                    title=f"Top 10 Largest Victories for {team} by Runs",
                    color='outcome_type',  # Color by margin (optional)
                    color_continuous_scale=px.colors.sequential.Viridis,
                    hover_data={'match_id': True}
                )
                
                st.plotly_chart(fig_largest_victories)

                
        with col2:

             query=f"""SELECT md.season, SUM(d.runs_batter) AS total_runs
                    FROM deliveries d
                    JOIN registry r ON d.batter = r.person_id
                    JOIN match_details md ON d.match_id = md.match_id
                    WHERE r.person_name = '{player_name}'
                    { "AND md.match_type = '"+match_type+"'" if match_type != "All" else ""}
                    GROUP BY md.season
                    ORDER BY total_runs DESC;"""
             query=f"""SELECT
        r.person_name,
        SUM(CASE WHEN d.fielders_involved = r.person_id THEN 1 ELSE 0 END) AS dismissals,
        SUM(CASE WHEN d.batter=r.person_id THEN d.runs_batter ELSE 0 END) AS total_runs,
        SUM(CASE WHEN d.bowler = r.person_id and player_out is not null THEN 1 ELSE 0 END) AS total_wickets
    FROM deliveries d
    JOIN registry r ON d.batter = r.person_id OR d.fielders_involved = r.person_id OR d.bowler = r.person_id
    JOIN match_details md ON d.match_id = md.match_id
    WHERE (team1 = %s OR team2 = %s) { "AND md.match_type = '"+match_type+"'" if match_type != "All" else ""}
    GROUP BY r.person_name
    """
             df=load_data(query,(team,team,))
             if not df.empty:
                 #print(df)
                 top_wicket_keeper = df.nlargest(1, 'dismissals')
                 top_batsman = df.nlargest(1, 'total_runs')
                 top_bowler = df.nlargest(1, 'total_wickets')                
                 
                     
                 if not top_wicket_keeper.empty:
                     st.metric("Top Wicket-Keeper", top_wicket_keeper['person_name'].iloc[0], top_wicket_keeper['dismissals'].iloc[0],border=True)
                 else:
                     st.write("No wicket-keeper information available.")



                 if not top_batsman.empty:
                     st.metric("Top Batsman", top_batsman['person_name'].iloc[0], top_batsman['total_runs'].iloc[0],border=True)
                 else:
                     st.write("No batsman information available.")



                 if not top_bowler.empty:
                     st.metric("Top Bowler", top_bowler['person_name'].iloc[0], top_bowler['total_wickets'].iloc[0],border=True)
                 else:
                     st.write("No bowler information available.")

                 
             else:
                 st.write("no data to display")

    else:
        st.warning("Please choose a team name from the sidebar dropdown")
 
    



