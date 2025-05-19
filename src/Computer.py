import logging

from lichess import schemas, LichessClient

from event_types import IncomingEvent
from Game import Game


logger = logging.getLogger(__name__)


class Computer:
    def __init__(self, /, token: str, **kwargs):
        self.client = LichessClient(token)

    def run(self, /):
        incoming_events = self.client.stream_incoming_events()
        for event in incoming_events:
            if event is None:
                continue
            self.handle_event(event)

    def handle_event(self, event: IncomingEvent):
        logger.info(f"Incoming event: {event.type}")
        match event.type:
            case "challenge":
                self.handle_challenge(event.challenge)
            case "gameStart":
                self.handle_game_start(event.game)

    def handle_challenge(self, /, challenge: schemas.ChallengeJson):
        logger.info(f"New challenge: {challenge.id}")
        if challenge.variant.key != "standard":
            self.client.decline_challenge(challenge.id, "standard")
            return

        time_control = challenge.timeControl

        if time_control.type != "clock":
            self.client.decline_challenge(challenge.id, "timeControl")
            return

        limit = time_control.limit
        increment = time_control.increment

        if (limit + increment * 100) < 300:
            self.client.decline_challenge(challenge.id, "tooFast")
            return

        self.client.accept_challenge(challenge.id)

    def handle_game_start(self, event_game: schemas.GameEventInfo):
        game_id = event_game.id
        opponent_name = event_game.opponent.username
        self.client.bot_write_game_chat_message(game_id, "player", f"Good luck, {opponent_name}!")

        game = Game(self.client, event_game)
        game.start()
