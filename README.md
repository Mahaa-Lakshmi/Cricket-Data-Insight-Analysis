# Cricsheet Match Data Analysis

## Overview

This project analyzes cricket match data from Cricsheet (https://cricsheet.org/) to derive insights into player performance, team statistics, and match outcomes.  The datasets for T20, Test, and ODI matches were directly downloaded from the Cricsheet website.  The project leverages Python with libraries like Pandas, Plotly for data processing and EDA, MySQL for database management and analysis, and Streamlit for creating an interactive web application.  A parallel visualization effort was also undertaken in Power BI to explore alternative dashboarding capabilities.

## Skills Takeaway

* **Data Processing with Python:**  Proficient in working with JSON files and transforming data into structured formats using Pandas.
* **Database Management with SQL:**  Experience in creating tables, inserting data, and writing optimized SQL queries.
* **Data Analysis:**  Utilized SQL to derive insights from cricket data through analytical queries.
* **Data Visualization:** Created interactive dashboards using Streamlit and explored visualization options in Power BI.
* **Exploratory Data Analysis (EDA):** Performed EDA using Python libraries like Plotly to uncover data patterns and trends.
* **Data Preprocessing:** Cleaned and organized raw JSON data into meaningful structures.
* **Streamlit Development:** Built an interactive web application for data exploration and visualization.
* **Power BI Dashboarding:**  Designed and implemented visualizations in Power BI.

## Domain

Sports Analytics / Data Analysis

## Problem Statement

This project aims to provide a comprehensive analysis of cricket match data.  By processing, analyzing, and visualizing data from Cricsheet, the project seeks to uncover key performance indicators, team trends, and insights into match dynamics.  The interactive Streamlit application and the Power BI dashboard enable users to explore the data and gain a deeper understanding of cricket matches.

## Business Use Cases

* **Player Performance Analysis:** Analyze players' performance across different match formats (Test, ODI, T20).
* **Team Insights:** Compare team performance over time and across match types.
* **Match Outcomes:** Understand win/loss patterns, margin of victories, and trends.
* **Umpiring Details:** Assist management in making informed decisions about the umpiring.
* **Strategic Decision-Making:** Assist analysts, coaches, and management in making informed decisions.
* **Fan Engagement:** Provide interactive platforms for fans to explore match data and statistics.

## Approach

1. **Data Acquisition:** Datasets for T20, Test, and ODI matches were directly downloaded from Cricsheet (https://cricsheet.org/matches/).

2. **Data Transformation:**
    * JSON files were parsed using Python's Pandas library.
    * Separate DataFrames were created for each match type.
    * Data was categorized into five tables: `players`, `officials`, `registry`, `match_details`, and `deliveries`.
    * Data was cleaned and preprocessed for analysis.

3. **Database Management:**
    * An MySQL database was used to store the data.
    * The following tables were created:
        * `players`: Stores information about players (name, team, match_id).
        * `officials`: Stores information about match officials (umpires, referee).
        * `registry`: Stores match registry details (person id and person name).
        * `match_details`: Stores overall match details (teams, toss, result, venue etc.).
        * `deliveries`: Stores ball-by-ball delivery information (batsman, bowler, runs, etc.).
    * Data was inserted into the respective tables.

4. **SQL Queries for Data Analysis:**
    * Over 10 SQL queries were written to extract insights from the data.  Examples include (but are not limited to):
        * Top 10 batsmen by total runs in ODI matches.
        * Leading wicket-takers in T20 matches.
        * Team with the highest win percentage in Test cricket.

5. **Exploratory Data Analysis (EDA) with Python:**
    * Python libraries like Plotly were used to create visualizations.
    * Visualizations included heatmaps, bar charts, scatter plots, line graphs, metric displays, donut charts, and pie charts.

6. **Streamlit Application:**
    * An interactive Streamlit application was developed to present the data and visualizations.
    * The application allows users to explore the data through interactive charts and tables.

7. **Power BI Dashboard (Parallel Effort):**
    * A Power BI dashboard was also created to explore alternative visualization approaches.
    * This dashboard aimed to replicate some of the insights presented in the Streamlit application.

## Results

* Processed and cleaned datasets for T20, Test, and ODI matches.
* Structured SQL database with tables.
* SQL queries to analyze player and team performance metrics.
* Interactive Streamlit application with a variety of visualizations.
* Power BI dashboard showcasing key insights.

## Technical Tags

Python, Pandas, MySQL, Streamlit, Plotly, Power BI, JSON, Data Analysis, EDA

## Dataset

* **Source:** Cricsheet Match Data (https://cricsheet.org/matches/)
* **Format:** JSON files for individual cricket matches (downloaded directly)
* **Variables:** Player statistics (runs, wickets), match results, teams, overs, deliveries, and more.

## Dataset Explanation

Each JSON file represents a cricket match and contains data such as:

* Match metadata: Teams, venue, date, toss result.
* Innings data: Runs, wickets, overs, and deliveries.
* Player details: Individual performance (batting, bowling).

## Project Deliverables

* **Python Source Code:**
    * Data processing and transformation scripts.
    * SQL insertion and query execution scripts.
    * Streamlit application code.
* **SQL Database:** MySQL database.
* **SQL Query File:** SQL queries used for table creations and data analysis.
* **Streamlit Application:** Deployed or readily runnable Streamlit application.
* **Power BI Dashboard:** Power BI file (.pbix).
* **README.md:** This file.
