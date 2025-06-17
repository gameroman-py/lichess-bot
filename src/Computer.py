import logging
from requests import HTTPError

from lichess import LichessClient, schemas
from lichess.custom import ApiStreamEvent

from Game import Game


logger = logging.getLogger(__name__)


class Computer:
    def __init__(self, /, token: str):
        self.client = LichessClient(token)

    def run(self, /):
        incoming_events = self.client.stream_incoming_events()
        for event in incoming_events:
            try:
                self.handle_event(event)
            except HTTPError as e:
                logging.exception(
                    f"HTTPError Error in handle_event (error code: {e.response.status_code})"
                )

    def handle_event(self, event: ApiStreamEvent):
        logger.info(f"Incoming event: {event.type}")
        match event.type:
            case "challenge":
                self.handle_challenge_event(event)
            case "gameStart":
                self.handle_game_start(event.game)
            case "challengeDeclined":
                logger.info(f"Challenge decline reason: {event.challenge.declineReasonKey}")
            case _:
                pass

    def handle_challenge_event(self, /, event: schemas.ChallengeEvent):
        challenge = event.challenge

        logger.info(f"New challenge: {challenge.id}")

        if event.compat and not event.compat.bot:
            self.client.decline_challenge(challenge.id, "tooFast")
            return

        if challenge.variant.key != "standard":
            self.client.decline_challenge(challenge.id, "standard")
            return

        if challenge.timeControl.type != "clock":
            self.client.decline_challenge(challenge.id, "timeControl")
            return

        self.client.accept_challenge(challenge.id)

    def handle_game_start(self, event_game: schemas.GameEventInfo):
        logger.info(f"New game started: {event_game.id}")
        Game(self.client, event_game).start()
