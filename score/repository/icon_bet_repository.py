from iconservice import *


class IconBetDB:
  _GAME_ON = "game_on"
  _TREASURY_SCORE = 'treasury_score'

  def __init__(self, db: IconScoreDatabase) -> None:
    self._game_on = VarDB(self._GAME_ON, db, value_type=bool)
    self._iconbet_score = VarDB(self._TREASURY_SCORE, db, value_type=Address)

  @property
  def game_on(self):
    return self._game_on

  @property
  def iconbet_score(self):
    return self._iconbet_score
