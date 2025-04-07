import connexion
from connexion import NoContent
import yaml
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
import os
import datetime
import httpx
import json
from datetime import datetime, timedelta

from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("stats.yml", base_path="/processing", strict_validation=True, validate_responses=True)
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

with open('/app/config/processing_app_conf.yml', 'r') as f:
        app_config = yaml.safe_load(f.read())

with open("/app/config/processing_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

def populate_stats():
    # print("In function populate stats!")

    # set up start and end timestamps
    logger.info(f"Periodic processing has started")
    if not os.path.exists('/app/data/stats.json'):
         start = "2024-02-12 20:10:14"
         end = "2026-02-12 20:10:14"
    else:
        with open('/app/data/stats.json', 'r') as file:
            data = json.load(file)
        last_updated = data.get("last_updated")
        end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # we need this bc if we take the timestamp from last stats, it will include last stats
        last_updated = datetime.fromisoformat(last_updated.rstrip("Z"))
        last_updated = last_updated + timedelta(seconds=1)
        start = last_updated

    print(start)
    print(end)

    # send da get request
    url = f"http://storage:8090/storage/nba/games?start_timestamp={start}&end_timestamp={end}"
    try:
        response = httpx.get(url)
        logger.info(f"Response for game event has status 200")
        
    except httpx.RequestError as exc:
        print(f"Error: {exc}")
        logger.info(f"Response for event has status 500")
        return

    games = response.json()

    url = f"http://storage:8090/storage/nba/players?start_timestamp={start}&end_timestamp={end}"
    try:
        response = httpx.get(url)
        logger.info(f"Response for player event has status 200")
        
    except httpx.RequestError as exc:
        print(f"Error: {exc}")
        logger.info(f"Response for event has status 500")
        return

    players = response.json()

    logger.info(f"Received {len(games)} game events")
    logger.info(f"Received {len(players)} player events")
    #only create statistics if there is statistics

    # if len(players) > 0 or len(games) > 0:
    # find max points and assists from player events
    max_points = 0
    max_assists = 0

    if not os.path.exists('/app/data/stats.json'):
        num_game_events = 0
        num_player_events = 0
        max_points = 0
        max_assists = 0
        lupdated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        with open('/app/data/stats.json', 'r') as file:
            data = json.load(file)
        num_game_events = data['num_game_events']
        num_player_events = data['num_player_events']
        max_points = data['max_points']
        max_assists = data['max_assists']
        lupdated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for player in players:
        points = int(player['points'])
        assists = int(player['assists'])

        if points > max_points:
            max_points = points
        if assists > max_assists:
            max_assists = assists

    STATISTICS = {
        "num_game_events":num_game_events + len(games),
        "num_player_events":num_player_events + len(players),
        "max_points": max_points,
        "max_assists": max_assists,
        "last_updated": lupdated
    }

    print(STATISTICS)

    with open('/app/data/stats.json', 'w') as file:
        json.dump(STATISTICS, file, indent=4)
    
    logger.debug(f"Updated Statistics: {STATISTICS}")
    logger.info(f"Period processing has ended")

def get_stats():
    logger.info(f"Request Received")
    if os.path.exists('/app/data/stats.json'):
        with open('/app/data/stats.json', 'r') as file:
            data = json.load(file)
        logger.debug(f"Contents: {data}")
        logger.info(f"Request completed")
        return data
    else:
        logger.error(f"Statistics do not exist")
        return 404


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
        'interval',
        seconds=app_config['scheduler']['interval'])
    sched.start()

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8092, host="0.0.0.0")
