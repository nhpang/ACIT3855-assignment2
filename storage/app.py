import connexion
from connexion import NoContent
from pathlib import Path
import json
from datetime import datetime
from models import NBAPlayers, NBAGames
from db import make_session
from  create_db import create_tables
import logging.config
import yaml
from datetime import datetime
import functools
from sqlalchemy import select
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


# def add_game(body):
#     file_path = Path("events.json")

#     # check if json file exist, if not, make
#     if not file_path.is_file():
#         file_path.touch()

#         data = {
#             "games_added":0,
#             "recent_games":[],
#             "player_stats_added":0,
#             "recent_stats":[]
#         }

#         with file_path.open("w") as file:
#             json.dump(data, file, indent=4)
    
#     # read json
#     with file_path.open("r") as file:
#         data = json.load(file)
    
#     # add to counter
#     data["games_added"] += 1

#     # add to msg
#     now = datetime.now()
#     time = now.strftime("%Y-%m-%d %H:%M:%S.%f")

#     new_data = {
#         "msg_data": body["game_id"] + " game added. Game score is " + str(body["team_1_score"]) + "-" + str(body["team_2_score"]),
#         "received_timestamp":time
#     }

#     max_events=5
#     event_file=data["recent_games"]

#     event_file.insert(0, new_data)

#     # check if theres 5 logs
#     while len(event_file) > max_events:
#          event_file.pop()

#     # write
#     with file_path.open("w") as file:
#             json.dump(data, file, indent=4)

# def add_player(body):
#     file_path = Path("events.json")

#     # check if json file exist, if not, make
#     if not file_path.is_file():
#         file_path.touch()

#         data = {
#             "games_added":0,
#             "recent_games":[],
#             "player_stats_added":0,
#             "recent_stats":[]
#         }

#         with file_path.open("w") as file:
#             json.dump(data, file, indent=4)
    
#     # read json
#     with file_path.open("r") as file:
#         data = json.load(file)
    
#     # add to counter
#     data["player_stats_added"] += 1

#     # add to msg
#     now = datetime.now()
#     time = now.strftime("%Y-%m-%d %H:%M:%S.%f")

#     new_data = {
#         "msg_data": str(body["player_id"]) + ' scored ' + str(body["points"]) + ' points in his most recent game',
#         "received_timestamp":time
#     }

#     max_events=5
#     event_file=data["recent_stats"]

#     event_file.insert(0, new_data)

#     # check if theres 5 logs
#     while len(event_file) > max_events:
#          event_file.pop()

#     # write
#     with file_path.open("w") as file:
#             json.dump(data, file, indent=4)

# ----------------------------------------------------------------------------------------------

def gameEvent(body):
    obj = NBAGames(
        # game_id=body["game_id"], 
        stadium_id=body["stadium_id"],
        team_1_id=body["team_1_id"],
        team_2_id=body["team_2_id"],
        team_1_score=body["team_1_score"],
        team_2_score=body["team_2_score"],
        timestamp=body["timestamp"],
        date_created=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        trace_id=body['trace_id'])
    session = make_session()
    session.add(obj)
    session.commit()
    session.close()

def playerEvent(body):
    obj = NBAPlayers(
        # statline_id=body['statline_id'],
        player_id=body["player_id"], 
        stadium_id=body["stadium_id"],
        points=body["points"],
        assists=body["assists"],
        rebounds=body["rebounds"],
        blocks=body["blocks"],
        steals=body["steals"],
        timestamp=body["timestamp"],
        date_created=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        trace_id=body['trace_id'])
    session = make_session()
    session.add(obj)
    session.commit()
    session.close()

# def use_db_session(func):
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         session = make_session()
#         try:
#             return func(session, *args, **kwargs)
#         finally:
#             session.close()
#     return wrapper

# ----------------------------------------------------------------------------------------------

# def report_game_data(body):
#     # add_game(body)
#     gameEvent(body)
#     logger.info(f"Stored game event with a trace id of {body['trace_id']}")
#     return NoContent, 201

# def report_player_data(body):
#     # add_player(body)
#     playerEvent(body)
#     logger.info(f"Stored player event with a trace id of {body['trace_id']}")
#     return NoContent, 201

def process_messages():
    """Process event messages"""
    hostname = (f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}')
    client = KafkaClient(hosts=hostname)
    topic = client.topics[(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(
        consumer_group=b'event_group',
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST
    )
    
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]

        if msg["type"] == "PlayerReport":
            playerEvent(payload)  # Store player event in DB
            logger.info(f"Stored player event with a trace id of {payload['trace_id']}")
        elif msg["type"] == "GameReport":
            gameEvent(payload)  # Store game event in DB
            logger.info(f"Stored game event with a trace id of {payload['trace_id']}")

        consumer.commit_offsets()
        logger.info("Offsets committed")


# ----------------------------------------------------------------------------------------------
# get requests dont touch this

def get_game_data(start_timestamp, end_timestamp):
    session = make_session()
    start = datetime.fromisoformat(start_timestamp)
    end = datetime.fromisoformat(end_timestamp)
    statement = select(NBAGames).where(NBAGames.date_created >= start).where(NBAGames.date_created < end)
    
    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]
    session.close()
    logger.info("Found %d nba games (start: %s, end: %s)", len(results), start, end)
    # print(results)
    return results

def get_player_data(start_timestamp, end_timestamp):
    session = make_session()
    start = datetime.fromisoformat(start_timestamp)
    end = datetime.fromisoformat(end_timestamp)
    statement = select(NBAPlayers).where(NBAPlayers.date_created >= start).where(NBAPlayers.date_created < end)
    print(statement)
    
    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]
    session.close()
    logger.info("Found %d nba players (start: %s, end: %s)", len(results), start, end)
    return results

# ----------------------------------------------------------------------------------------------

with open('/app/config/storage_app_conf.yml', 'r') as f:
        app_config = yaml.safe_load(f.read())

with open("/app/config/storage_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

# ----------------------------------------------------------------------------------------------

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("basketball.yml",base_path="/storage",strict_validation=True,validate_responses=True)

def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon=True
    t1.start()

if __name__ == "__main__":
    create_tables()
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")