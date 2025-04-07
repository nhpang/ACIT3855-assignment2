import connexion
from connexion import NoContent
import httpx
import time
import yaml
import logging.config
import datetime
import json
from pykafka import KafkaClient

# def forward_to_storage(endpoint: str, body: dict, event_name):
#     try:
#         response = httpx.post(f"http://localhost:8090/{endpoint}", json=body)
#         # print('fortnite ', body)
#         logger.info(f"Response for event {event_name} (id: {body['trace_id']}) has status 201")
#         return NoContent, response.status_code
        
#     except httpx.RequestError as exc:
#         print(f"Error: {exc}")
#         logger.info(f"Response for event {event_name} (id: {body['trace_id']}) has status 500")
#         return {"error": "Could not reach storage service"}, 500

# def report_game_data(body):
#     trace_id = time.time_ns()
#     body['trace_id'] = trace_id
#     # print(body)
#     logger.info(f"Received game event with a trace id of {body['trace_id']}")

#     return forward_to_storage("nba/games", body, 'GameReport')

# def report_player_data(body):
#     trace_id = time.time_ns()
#     body['trace_id'] = trace_id
#     # print(body)
#     logger.info(f"Received player event with a trace id of {body['trace_id']}")
#     return forward_to_storage("nba/players", body, 'PlayerReport') 

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("basketball.yml", base_path="/receiver", strict_validation=True, validate_responses=True)

with open('/app/config/receiver_app_conf.yml', 'r') as f:
        app_config = yaml.safe_load(f.read())

with open("/app/config/receiver_log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

# set the variables

kafka_hostname = app_config["events"]["hostname"]
kafka_port = app_config["events"]["port"]
kafka_topic = app_config["events"]["topic"]

client = KafkaClient(hosts=f"{kafka_hostname}:{kafka_port}")
topic = client.topics[str.encode(kafka_topic)]
producer = topic.get_sync_producer()

# send to kafka function
def send_to_kafka(event_type, body):

    # add trace id (from old code)
    trace_id = time.time_ns()
    body["trace_id"] = trace_id
    logger.info(f"Received {event_type} event with trace id {trace_id}")

    # prep msg
    msg = {
        "type": event_type,
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }

    # send message
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    return NoContent, 201

def report_game_data(body):
    return send_to_kafka("GameReport", body)

def report_player_data(body):
    return send_to_kafka("PlayerReport", body)

if __name__ == "__main__":
    app.run(port=8091, host="0.0.0.0")
