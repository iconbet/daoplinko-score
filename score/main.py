from iconservice import *
from .repository.icon_bet_repository import *
from .game.consts import *

TAG = 'DAOplinko'


# ================================================
# An interface to roulette score
# ================================================
class TreasuryInterface(InterfaceScore):
    @interface
    def send_wager(self, _amount: int) -> None:
        pass

    @interface
    def wager_payout(self, _payout: int) -> None:
        pass


# ================================================
#  Exceptions
# ================================================
class InvalidStartingSelection(Exception):
    pass


class InvalidOption(Exception):
    pass


class DAOplinko(IconScoreBase):
    _NAME = "DAOplinko"
    _ADMIN_ADDRESS = "Admin_Address"

    @eventlog(indexed=2)
    def LandingBucketResult(self, bucket_position: int, random_number: int) -> None:
        pass

    @eventlog(indexed=2)
    def SideBetResult(self, result: str, random_number: int) -> None:
        pass

    # ================================================
    #  Event Logs
    # ================================================
    @eventlog(indexed=2)
    def BetSource(self, _from: Address, timestamp: int):
        pass

    @eventlog(indexed=2)
    def FundTransfer(self, recipient: Address, amount: int, note: str):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        self._name = DAOplinko._NAME
        self._iconBetDB = IconBetDB(db)
        self._treasury_score = self.create_interface_score(self._iconBetDB.iconbet_score.get(), TreasuryInterface)
        self._game_admin = VarDB(self._ADMIN_ADDRESS, db, value_type=Address)
        self._db = db

        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return self._name

    # ================================================
    #  Internal methods
    # ================================================
    def _validate_bet(self, bet_amount: int, side_bet_set: bool, side_bet_amount: int, side_bet_bucket: int) -> None:
        # validate bet_amount min and max
        if bet_amount < BET_MIN:
            revert(f'Invalid Min Bet: Min allowed is 1 ICX')
        if bet_amount > MAX_BET:
            revert(f'Invalid Max Bet: Max allowed is 100 ICX')

        if side_bet_set:
            if side_bet_amount < BET_MIN:
                revert(f'Invalid Side Bet Min Bet: Min allowed is 1 ICX')
            if side_bet_amount > MAX_SET_BET:
                revert(f'Invalid Side Bet Max Bet: Max allowed is 25 ICX')
            if side_bet_bucket not in [0, 1, 2, 3, 4, 5]:
                revert(f'Invalid Side Bet Bucket Selected: Choose between 0-5')

    def _get_random(self, user_seed: str) -> int:
        # generates a random number between 0 - 42
        seed = (str(bytes.hex(self.tx.hash)) + str(self.now()) + user_seed)
        r_number = (int.from_bytes(sha3_256(seed.encode()), "big") % 43) / 1
        return int(r_number)

    def _determinte_side_bet_win(self, b_setup: int, landing_bucket: int, side_bet_amount: int, side_bet_bucket: int) -> int:
        if landing_bucket == side_bet_bucket:
            if b_setup == 1:
                return int(side_bet_amount * (SIDE_BET_MULTIPLIERS[0][landing_bucket] // 1000))
            elif b_setup == 2:
                return int(side_bet_amount * (SIDE_BET_MULTIPLIERS[1][landing_bucket] // 1000))
            elif b_setup == 3:
                return int(side_bet_amount * (SIDE_BET_MULTIPLIERS[2][landing_bucket] // 1000))
        else:
            return 0

    def _bet(self, b_setup: int, bet_amount: int, side_bet_amount: int, side_bet_bucket: int, user_seed: str) -> None:
        if self._iconBetDB.game_on.get():
            side_bet_set = False
            landing_bucket = -1
            if side_bet_amount > 0:
                side_bet_set = True
            # determine size of the main bet (tx value - side_bet)
            bet_amount = bet_amount - side_bet_amount
            self._validate_bet(bet_amount, side_bet_set, side_bet_amount, side_bet_bucket)

            rand = self._get_random(user_seed)

            # BET 10
            # PRIZE		    25	5	50	0	15	10
            # PROBABILITY	4	10	1	10	8	10   / 43 * 100
            if b_setup == 1:
                if 0 <= rand <= 9:
                    self.LandingBucketResult(3, rand)
                    self._send_wager(bet_amount)
                    landing_bucket = 3
                elif 10 <= rand <= 17:
                    self.LandingBucketResult(4, rand)
                    payout = int(bet_amount * (MULTIPLIERS[0][4] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 4
                elif rand == 18:
                    self.LandingBucketResult(2, rand)
                    payout = int(bet_amount * (MULTIPLIERS[0][2] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 2
                elif 19 <= rand <= 22:
                    self.LandingBucketResult(0, rand)
                    payout = int(bet_amount * (MULTIPLIERS[0][0] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 0
                elif 23 <= rand <= 32:
                    self.LandingBucketResult(1, rand)
                    payout = int(bet_amount * (MULTIPLIERS[0][1] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 1
                elif 33 <= rand <= 42:
                    self.LandingBucketResult(5, rand)
                    payout = int(bet_amount * (MULTIPLIERS[0][5] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 5

            # BET 10
            # PRIZE		    10	50	0	0	50	10
            # PROBABILITY	11	2	8	9	2	11   / 43 * 100
            elif b_setup == 2:
                if 0 <= rand <= 10:
                    self.LandingBucketResult(0, rand)
                    payout = int(bet_amount * (MULTIPLIERS[1][0] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 0
                elif 11 <= rand <= 12:
                    self.LandingBucketResult(1, rand)
                    payout = int(bet_amount * (MULTIPLIERS[1][1] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 1
                elif 13 <= rand <= 20:
                    self.LandingBucketResult(2, rand)
                    self._send_wager(bet_amount)
                    landing_bucket = 2
                elif 21 <= rand <= 29:
                    self.LandingBucketResult(3, rand)
                    self._send_wager(bet_amount)
                    landing_bucket = 3
                elif 30 <= rand <= 31:
                    self.LandingBucketResult(4, rand)
                    payout = int(bet_amount * (MULTIPLIERS[1][4] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 4
                elif 32 <= rand <= 42:
                    self.LandingBucketResult(5, rand)
                    payout = int(bet_amount * (MULTIPLIERS[1][5] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 5
            # BET 10
            # PRIZE		    15	35	4	5	20	13
            # PROBABILITY	8	1	12	11	3	8   / 43 * 100
            elif b_setup == 3:
                if 0 <= rand <= 7:
                    self.LandingBucketResult(0, rand)
                    payout = int(bet_amount * (MULTIPLIERS[2][0] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 0
                elif rand == 8:
                    self.LandingBucketResult(1, rand)
                    payout = int(bet_amount * (MULTIPLIERS[2][1] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 1
                elif 9 <= rand <= 20:
                    self.LandingBucketResult(2, rand)
                    payout = int(bet_amount * (MULTIPLIERS[2][2] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 2
                elif 21 <= rand <= 31:
                    self.LandingBucketResult(3, rand)
                    payout = int(bet_amount * (MULTIPLIERS[2][3] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 4
                elif 32 <= rand <= 34:
                    self.LandingBucketResult(4, rand)
                    payout = int(bet_amount * (MULTIPLIERS[2][4] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 4
                elif 35 <= rand <= 42:
                    self.LandingBucketResult(5, rand)
                    payout = int(bet_amount * (MULTIPLIERS[2][5] // 10))
                    self._send_wager_and_payout(bet_amount, payout)
                    landing_bucket = 5

            if landing_bucket < 0:
                revert("Landing bucket error returning bet")

            # determine side bet payout
            if side_bet_set:
                side_bet_payout = self._determinte_side_bet_win(b_setup, landing_bucket, side_bet_amount, side_bet_bucket)
                if side_bet_payout > 0:
                    self.SideBetResult("WIN", landing_bucket)
                    payout = side_bet_payout
                    self._send_wager_and_payout(side_bet_amount, payout)
                else:
                    self.SideBetResult("LOST", landing_bucket)
                    self._send_wager(side_bet_amount)
        else:
            revert("Game is currently off")

    def _send_wager_and_payout(self, bet_amount: int, payout_amount: int) -> None:
        try:
            self.FundTransfer(self._iconBetDB.iconbet_score.get(), self.msg.value, "Sending icx to Treasury")
            # send wager to treasury
            self.icx.transfer(self._iconBetDB.iconbet_score.get(), self.msg.value)
            self._treasury_score.send_wager(bet_amount)
            # send payout request to treasury
            self._treasury_score.wager_payout(payout_amount)
        except BaseException as e:
            revert('Network problem. Winnings not sent. Returning funds.')

    def _send_wager(self, bet_amount: int) -> None:
        # send wager to treasury
        try:
            self.FundTransfer(self.tx.origin, self.msg.value, "Sending icx to Treasury")
            self.icx.transfer(self._iconBetDB.iconbet_score.get(), self.msg.value)
            self._treasury_score.send_wager(bet_amount)
        except BaseException as e:
            revert('Network problem. Wager not sent. Returning funds.')

    # ================================================
    #  External methods
    # ================================================
    @payable
    @external
    def bet(self, b_setup: int, side_bet_amount: int = 0, side_bet_bucket: int = 0, user_seed: str = "") -> None:
        bet_amount = self.msg.value
        self._bet(b_setup, bet_amount, side_bet_amount, side_bet_bucket, user_seed)

    @external(readonly=True)
    def get_min_bet_allowed(self) -> int:
        return BET_MIN

    @external(readonly=True)
    def get_max_bet_allowed(self) -> int:
        return MAX_BET

    @external
    def set_treasury_score(self, score: Address) -> None:
        """
        Sets the treasury score address. The function can only be invoked by score owner.
        :param score: Score address of the treasury
        :type score: :class:`iconservice.base.address.Address`
        """
        if self.msg.sender == self.owner:
            self._iconBetDB.iconbet_score.set(score)

    @external(readonly=True)
    def get_treasury_score(self) -> Address:
        """
        Returns the treasury score address.
        :return: Address of the treasury score
        :rtype: :class:`iconservice.base.address.Address`
        """
        return self._iconBetDB.iconbet_score.get()

    @external(readonly=True)
    def get_game_on_status(self) -> bool:
        return self._iconBetDB.game_on.get()

    @external(readonly=True)
    def get_score_owner(self) -> Address:
        """
        A function to return the owner of the score
        :return:Address
        """
        return self.owner

    @external
    def turn_game_on(self):
        game_admin = self._game_admin.get()
        if self.msg.sender != game_admin:
            revert('Only the game admin can call the game_on method')
        if not self._iconBetDB.game_on.get() and self._iconBetDB.iconbet_score.get() is not None:
            self._iconBetDB.game_on.set(True)

    @external
    def turn_game_off(self):
        game_admin = self._game_admin.get()
        if self.msg.sender != game_admin:
            revert('Only the game admin can call the game_on method')
        if self._iconBetDB.game_on.get():
            self._iconBetDB.game_on.set(False)

    @external
    def set_game_admin(self, admin_address: Address) -> None:
        if self.msg.sender != self.owner:
            revert('Only the owner can call set_game_admin method')
        self._game_admin.set(admin_address)

    @external(readonly=True)
    def get_game_admin(self) -> Address:
        """
        A function to return the admin of the game
        :return: Address
        """
        return self._game_admin.get()

    @external(readonly=True)
    def get_bucket_multipliers(self) -> str:
        return json_dumps(MULTIPLIERS_FLOAT)

    @external(readonly=True)
    def get_side_multipliers(self) -> str:
        return json_dumps(SIDE_BET_MULTIPLIERS_FLOAT)

    @external(readonly=True)
    def get_bucket_odds(self) -> str:
        return json_dumps(BUCKET_ODDS)

    def fallback(self):
        pass