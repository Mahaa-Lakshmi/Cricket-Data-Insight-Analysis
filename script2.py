import json
import os
import mysql.connector
from concurrent.futures import ThreadPoolExecutor
import logging
import datetime

# Configure logging
log_file = "insertion_log4.txt"  # Specify your log file
logging.basicConfig(filename=log_file, level=logging.INFO,  # Set logging level
                    format='%(asctime)s - %(levelname)s - %(message)s')


def insert_with_autocommit(data, table_name, cnx): # pass the connection object.
    """Inserts with autocommit using mysql.connector."""
    cursor = cnx.cursor()
    try:
        columns = ", ".join(data.keys())
        values = ", ".join([f"%({key})s" for key in data.keys()])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
        cursor.execute(query, data)
        #logging.info(f"Inserted into {table_name}: {data}")
    except mysql.connector.IntegrityError as e: # catch integrity error.
        logging.error(f"Integrity Error inserting into {table_name}: {e} Data: {data}")
        return False # return false if it fails.
    except Exception as e:
        logging.error(f"Error inserting into {table_name}: {e} Data: {data}")
        return False # return false if it fails.
    finally:
        cursor.close()

    return True # return True if it is successful.


def process_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            matchID = os.path.basename(filepath).split('.')[0]

            d = data.get('info', {})
            registry = d.get('registry', {}).get('people', {})

            # Establish connection (inside the function for each thread)
            mydb = mysql.connector.connect(host="localhost", user="root", password="root", database="cricket_dataset_practice", autocommit=False) # autocommit is set to false.


            try:
                # ✅ Insert `registry` (autocommit for each successful insert)
                for person_name, person_id in registry.items():
                    registry_data = {"person_id": person_id, "person_name": person_name}
                    if not insert_with_autocommit(registry_data, "registry", mydb): # check if insert is successful.
                        continue # if insert is not successful, then continue to the next record.
                mydb.commit() # commit the registry insert if it is successful.

                # Start a transaction for other tables
                mydb.start_transaction()

                # ✅ Insert `match_details`

                player_of_match_list = [registry.get(i) for i in d.get("player_of_match", [])]  # Get IDs, handle missing

                # Convert to comma-separated string, handling None values correctly
                player_of_match_str = ", ".join(
                    [str(player_id) for player_id in player_of_match_list if player_id is not None]
                )

                match = {
                    "match_id": matchID,
                    "city": d.get('city', None),
                    "gender": d.get('gender', None), 
                    "match_type": d.get('match_type', None), 
                    "match_type_number": d.get('match_type_number', None), 
                    "overs": d.get('overs', None), 
                    "season": d.get('season', None), 
                    "team_type": d.get('team_type', None), 
                    "venue": d.get('venue', None),
                    "team1": d.get("teams", [None, None])[0],
                    "team2": d.get("teams", [None, None])[1],
                    "toss_winner": d.get("toss", {}).get("winner", None),
                    "toss_decision": d.get("toss", {}).get("decision", None),
                    "winner": d.get("outcome", {}).get("winner", None), 
                    "outcome_type" : list(d.get("outcome", {}).get("by", {}).keys())[0] if d.get("outcome", {}).get("by") else d.get("outcome", {}).get("result") if d.get("outcome", {}).get("result") else None,
                    "outcome_value" : list(d.get("outcome", {}).get("by").values())[0] if d.get("outcome", {}).get("by") else None,
                    "player_of_match": player_of_match_str if player_of_match_str else None,
                    "balls_per_over": d.get("balls_per_over", None)
                }
                if match.get("player_of_match"):  # Check if player_of_match exists
                    cursor = mydb.cursor()
                    cursor.execute("SELECT 1 FROM registry WHERE person_id = %s", (match["player_of_match"],))
                    player_exists = cursor.fetchone() is not None
                    cursor.close()

                    if not player_exists:
                        logging.error(f"player_of_match '{match['player_of_match']}' not found in registry!")
                        # Decide how to handle: skip insert, set player_of_match to None, etc.
                        match["player_of_match"] = None  # Example: set to None to allow the insert
                        # or
                        # return  # Skip processing the rest of the match
                insert_with_autocommit(match, "match_details", mydb)
                #print("completed insert of match details",matchID)

                # ✅ Insert `officials`
                for off in d.get('officials', {}): 
                    for person in d['officials'][off]:
                        official_data = {"match_id": matchID, "person_id": registry.get(person, None), "official_type": off}
                        insert_with_autocommit(official_data, "officials", mydb)
                #print("comleted insert of officials",matchID)

                # ✅ Insert `players`
                for team, players in d.get('players', {}).items():
                    for player in players:
                        player_data = {"match_id": matchID, "person_id": registry.get(player, None), "team_name": team}
                        insert_with_autocommit(player_data, "players", mydb)
                #print("comleted insert of players",matchID)

                # ✅ Insert `deliveries`
                for inning_count, inning in enumerate(data.get('innings', []), start=1):
                    team, powerplays = inning['team'], {pp['type']: (int(pp['from']), int(pp['to'])) for pp in inning.get('powerplays', [])}
                    miscounted = {int(k): v['balls'] for k, v in inning.get('miscounted_overs', {}).items()}
                    for over in inning.get('overs', []):
                        over_num, balls_limit = over['over'], miscounted.get(over['over'], 6)
                        for ball_count, delivery in enumerate(over.get('deliveries', []), start=1):
                            if ball_count > balls_limit: continue  # Skip extra miscounted deliveries
                            powerplay_type = next((t for t, (s, e) in powerplays.items() if s <= over_num <= e), 'none')
                            delivery_data = {
                                "match_id": matchID,
                                "innings": inning_count,
                                "team": inning.get("team"),
                                "overs": over.get("over"),
                                "balls": ball_count,
                                "batter": registry.get(delivery.get("batter")),
                                "bowler": registry.get(delivery.get("bowler")),
                                "non_striker": registry.get(delivery.get("non_striker")),
                                "runs_batter": delivery.get("runs", {}).get("batter"),
                                "runs_extras": delivery.get("runs", {}).get("extras"),
                                "runs_total": delivery.get("runs", {}).get("total"),
                                'powerplayed': 'yes' if powerplay_type != 'none' else 'no',
                                'powerplayed_type': powerplay_type,
                                "player_out": registry.get(delivery.get("wickets", [{}])[0].get("player_out")),
                                "dismissal_kind": delivery.get("wickets", [{}])[0].get("kind")
                            }
                            insert_with_autocommit(delivery_data, "deliveries", mydb)
                
                #print("comleted insert of deliveries",matchID)
                mydb.commit()  # Commit other tables transaction

            except Exception as e: # catch the exception and rollback.
                mydb.rollback()
                logging.error(f"Error inserting other tables data: {e}")

            return matchID

    except Exception as e:
        logging.error(f"Error processing {filepath}: {e}")
        return None
    finally: # close the connection.
        if 'mydb' in locals() and mydb.is_connected():
            mydb.close()


def process_all_json_files_parallel(matches_path, formats, num_workers=50):
    """ Process JSON files in parallel using ThreadPoolExecutor. """
    all_files = []

    current_time = datetime.datetime.now()
    print("Started at - ",current_time.strftime("%Y-%m-%d %H:%M:%S"))

    for format_name in formats:
        format_path = os.path.join(matches_path, format_name)
        if os.path.isdir(format_path):
            files = [os.path.join(format_path, file) for file in os.listdir(format_path) if file.endswith(".json")]
            all_files.extend(files)
    print("Inside process_all_json_files_parallel")

    # ✅ Process files in parallel (limit to `num_workers` threads)
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_json_file, all_files))

    print(f"✅ Processed {len([r for r in results if r is not None])} matches successfully!")
    current_time = datetime.datetime.now()
    print("Ended at - ",current_time.strftime("%Y-%m-%d %H:%M:%S"))

# Example Usage:
matches_path = "matches"
formats = ["odis_json", "t20s_json", "tests_json"]
process_all_json_files_parallel(matches_path, formats, num_workers=50)