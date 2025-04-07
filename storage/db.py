from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import NBAPlayers, NBAGames
import functools
import yaml

with open('/app/config/storage_app_conf.yml', 'r') as f:
        config = yaml.safe_load(f.read())

engine = create_engine(f"mysql://{config['datastore']['user']}:{config['datastore']['password']}@{config['datastore']['hostname']}:{config['datastore']['port']}/{config['datastore']['db']}")


def make_session():
    return sessionmaker(bind=engine)()

