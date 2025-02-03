import mysql.connector as db
import pandas as pd
import plotly.express as px
import streamlit as st

class DatabaseManager:
    def __init__(self, host, port, user, password, database):
        # Database connection details
        self.cnx = db.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=True
        )

        self.db_curr = self.cnx.cursor(dictionary=True)
    
    def get_player_name(self,gender):
        query = """select distinct r.person_name
            from players p
            join registry r on p.person_id=r.person_id
            join match_details md on md.match_id=p.match_ID
            where gender=%s
            order by r.person_name;"""
        self.db_curr.execute(query,(gender,))
        person=[person['person_name'] for person in self.db_curr.fetchall()]     
        #print(person)   
        return person
    
    def get_total_Runs(self,query):
        self.db_curr.execute(query)
        #print(self.db_curr.fetchall())
        total_runs=self.db_curr.fetchall()[0].get("total_runs")
        return str(total_runs)
    
    def get_batting_Avg(self,query):
        self.db_curr.execute(query)
        rows=self.db_curr.fetchall()[0]
        person_name = rows.get("person_name")
        total_runs = rows.get("total_runs")
        dismissals = rows.get("dismissals")
        innings_played = rows.get("innings_played")

        if dismissals > 0:
            batting_average = total_runs / dismissals
            #print(f"Player: {person_name}, Overall Batting Average: {batting_average:.2f}")
            return f"{batting_average:.2f}"
        else:
            if innings_played > 0:
              batting_average = total_runs
              #print(f"Player: {person_name}, Overall Batting Average: {batting_average:.2f}*") # * indicates not out
              return f"{batting_average:.2f}"
            else:
                return "0.00"
              #print(f"Player: {person_name}, Overall Batting Average: N/A") # No innings played
       
    def get_total_wickets(self,query):
        self.db_curr.execute(query)
        #print(self.db_curr.fetchall())
        total_wickets=self.db_curr.fetchall()[0].get("total_wickets")
        return str(total_wickets)
    
    



