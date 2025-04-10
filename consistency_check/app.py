import connexion
from connexion import NoContent
import yaml
import logging.config
import os
import datetime
import httpx
import json
from datetime import datetime, timedelta
from pykafka import KafkaClient
from pykafka.common import OffsetType

from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("consistency_check.yml", base_path="/consistency_check", strict_validation=True, validate_responses=True)
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

with open('/app/config/consistency_check_app_conf.yml', 'r') as f:
        app_config = yaml.safe_load(f.read())

with open("/app/config/consistency_checkg_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

# -----------------------------------------------------------------------------------------------------------

def update_cc():
    print('updaters')

    counts = {}
    missdb = {}
    missqueue = {}

    # STORAGE ------------------------------- STORAGE


    # send da get request
    url = f"http://storage:8090/storage/nba/games?start_timestamp=2024-02-12 20:10:14&end_timestamp=2026-02-12 20:10:14"
    try:
        response = httpx.get(url)
        logger.info(f"Response for game event has status 200")
        
    except httpx.RequestError as exc:
        print(f"Error: {exc}")
        logger.info(f"Response for event has status 500")
        return

    games = response.json()

    url = f"http://storage:8090/storage/nba/players?start_timestamp=2024-02-12 20:10:14&end_timestamp=2026-02-12 20:10:14"
    try:
        response = httpx.get(url)
        logger.info(f"Response for player event has status 200")
        
    except httpx.RequestError as exc:
        print(f"Error: {exc}")
        logger.info(f"Response for event has status 500")
        return

    players = response.json()

    counts.update({'db': {
        "games": len(games),
        "players": len(players)
    }})

    print(games)
    print(players)


    # KAFKA ------------------------------------------- KAFKA

    """Process event messages"""
    hostname = f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}'
    topic_name = app_config["events"]["topic"]

    client = KafkaClient(hosts=hostname)
    topic = client.topics[topic_name.encode('utf-8')]  # Topic names must be bytes

    consumer = topic.get_simple_consumer(
        consumer_timeout_ms=1000,         # Timeout if no new messages
        auto_offset_reset=OffsetType.EARLIEST,  # Start from earliest message
        reset_offset_on_start=True       # Ensure offset reset happens
    )

    messages = []
    for message in consumer:
        if message is not None:
            messages.append(message.value.decode('utf-8'))  # Decode from bytes to string

    consumer.stop()
    print(messages)

    kafkapcount = 0
    kafkagcount = 0
    for i in messages:
        i = json.loads(i)
        if i['type'] == 'GameReport':
            kafkagcount += 1
            found = False
            for game in games:
                if game['trace_id'] == i['payload']['trace_id']:
                    found = True
                    break

            if not found:
                missdb.update({
                    "trace_id": i['payload']['trace_id'],
                    "team_1_id": i['payload']['team_1_id'],
                    "type": i['type']
                })  
        else:
            kafkapcount += 1
            found = False
            for player in players:
                if player['trace_id'] == i['payload']['trace_id']:
                    found = True
                    break

            if not found:
                missdb.update({
                    "trace_id": i['payload']['trace_id'],
                    "player_id": i['payload']['player_id'],
                    "type": i['type']
                })

        
        # MISSING FROM DB ----------------------------------------------- MISSING FROM DB

        

    counts.update({'queue': {
        "games": kafkagcount,
        "players": kafkapcount
    }})


    # PROCESSING -------------------------------------- PROCESSING

    url = f"http://processing:8092/processing/stats"
    try:
        response = httpx.get(url)
        logger.info(f"Response for processing event has status 200")
        
    except httpx.RequestError as exc:
        print(f"Error: {exc}")
        logger.info(f"Response for processing event has status 500")
        return

    processing = response.json()

    counts.update({'processing': {
        "games": processing['num_game_events'],
        "players": processing['num_player_events']
    }})

    # MISSING FROM QUEUE ----------------------------------------------- MISSING FROM QUEUE

    for event in players:
        found = False
        for i in messages:
            i = json.loads(i)
            if event['trace_id'] == i['payload']['trace_id']:
                found = True
                break

            if not found:
                missqueue.update({
                    "trace_id": event['trace_id'],
                    "statline_id": event['statline_id'],
                    "type": 'player'
                })

    for event in games:
        found = False
        for i in messages:
            i = json.loads(i)
            if event['trace_id'] == i['payload']['trace_id']:
                found = True
                break

            if not found:
                missqueue.update({
                    "trace_id": event['trace_id'],
                    "game_id": event['game_id'],
                    "type": 'game'
                })

    # -------------------------------------------------------------------------------------------------------------------------

    STATISTICS = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "counts": counts,
        "missing_in_db": missdb,
        "missing_in_queue": missqueue
    }

    print(STATISTICS)

    with open('/app/data/stats.json', 'w') as file:
        json.dump(STATISTICS, file, indent=4)

    return STATISTICS




def get_checks():
    with open('/app/data/stats.json', 'r') as file:
            data = json.load(file)
    return data
    pass



# -----------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(port=8094, host="0.0.0.0")
