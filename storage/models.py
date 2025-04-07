from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, func, BigInteger, inspect
from datetime import datetime

class Base(DeclarativeBase):
    pass

class NBAGames(Base):
    __tablename__ = "nbagames"
    game_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    stadium_id = mapped_column(String(50), nullable=False)
    team_1_id = mapped_column(String(50), nullable=False)
    team_2_id = mapped_column(String(50), nullable=False)
    team_1_score = mapped_column(Integer, nullable=False)
    team_2_score = mapped_column(Integer, nullable=False)
    timestamp = mapped_column(String(50), nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    trace_id = mapped_column(BigInteger, nullable=False)

    def to_dict(self):
        games = {
            "game_id" : str(self.game_id),
            "stadium_id" : self.stadium_id,
            "team_1_id" : self.team_1_id,
            "team_2_id" : self.team_2_id,
            "team_1_score" : self.team_1_score,
            "team_2_score" : self.team_2_score,
            "timestamp" : self.timestamp,
            "date_created" : self.date_created,
            "trace_id" : self.trace_id
        }

        return games
class NBAPlayers(Base):
    __tablename__ = "nbaplayers"
    statline_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id = mapped_column(String(100), nullable=False)
    stadium_id = mapped_column(String(50), nullable=False)
    
    points = mapped_column(Integer, nullable=False)
    assists = mapped_column(Integer, nullable=False)
    rebounds = mapped_column(Integer, nullable=False)
    blocks = mapped_column(Integer, nullable=False)
    steals = mapped_column(Integer, nullable=False)
    timestamp = mapped_column(String(50), nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    trace_id = mapped_column(BigInteger, nullable=False)

    def to_dict(self):
        player_stats = {
            "statline_id": str(self.statline_id),
            "player_id": self.player_id,
            "stadium_id": self.stadium_id,
            "points": self.points,
            "assists": self.assists,
            "rebounds": self.rebounds,
            "blocks": self.blocks,
            "steals": self.steals,
            "timestamp": self.timestamp,
            "date_created": self.date_created,
            "trace_id": self.trace_id
        }

        return player_stats