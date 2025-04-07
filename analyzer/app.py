import connexion
import logging.config
import yaml
from pykafka import KafkaClient
import json
import os

from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

# ----------------------------------------------------------------

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("analyzer.yml", base_path="/analyzer",strict_validation=True, validate_responses=True)
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ----------------------------------------------------------------

with open('/app/config/analyzer_app_conf.yml', 'r') as f:
        app_config = yaml.safe_load(f.read())

with open("/app/config/analyzer_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

# ----------------------------------------------------------------

kafka_hostname = app_config["events"]["hostname"]
kafka_port = app_config["events"]["port"]
kafka_topic = app_config["events"]["topic"]

# ----------------------------------------------------------------

def players(index):
    client = KafkaClient(hosts=f"{kafka_hostname}:{kafka_port}")
    topic = client.topics[str.encode(kafka_topic)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    counter = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data['type'] == 'PlayerReport':
             if counter == index:
                logger.info(f'Player data: {data}')
                return data
             counter = counter + 1
    
    logger.info(f"No message at index {index}!")
    return { "message": f"No message at index {index}!"}, 404

def games(index):
    client = KafkaClient(hosts=f"{kafka_hostname}:{kafka_port}")
    topic = client.topics[str.encode(kafka_topic)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    counter = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data['type'] == 'GameReport':
             if counter == index:
                logger.info(f'Game data: {data}')
                return data
             counter = counter + 1
    logger.info(f"No message at index {index}!")
    return { "message": f"No message at index {index}!"}, 404

def stats():
    client = KafkaClient(hosts=f"{kafka_hostname}:{kafka_port}")
    topic = client.topics[str.encode(kafka_topic)]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    
    gcounter = 0
    pcounter = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data['type'] == 'PlayerReport':
             pcounter = pcounter + 1
        if data['type'] == 'GameReport':
             gcounter = gcounter + 1

    return {"num_player_reports":pcounter, "num_game_reports":gcounter}

# ----------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8093)