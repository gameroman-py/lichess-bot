import lichess
from lichess import LichessClient

from Game import Game


class Computer:
    def __init__(self, /, token: str, **kwargs):
        self.client = LichessClient(token)
        self.incoming_events = self.client.stream_incoming_events()

    def run(self, /):
        try:
            for event in self.incoming_events:
                if event is None:
                    continue
                match event.type:
                    case "challenge":
                        self.handle_challenge(event.challenge)

                    case "gameStart":
                        event_game = event.game
                        game_id = event_game.id
                        opponent_name = event_game.opponent.username
                        self.client.bot_write_game_chat_message(
                            game_id, "player", f"Good luck, {opponent_name}!"
                        )

                        game = Game(self.client, event_game)
                        game.start()

                    case "gameFinish":
                        ...

                    case "challengeDeclined":
                        ...

                    case "challengeCanceled":
                        ...

        except Exception as e:
            print(e)

    def handle_challenge(self, /, challenge: lichess.schemas.ChallengeJson):
        decline = self.client.decline_challenge

        if challenge.variant.key != "standard":
            decline(challenge.id, "standard")
            return

        time_control = challenge.timeControl

        if time_control.type != "clock":
            decline(challenge.id, "timeControl")
            return

        limit = time_control.limit
        increment = time_control.increment

        if (limit + increment * 100) < 300:
            decline(challenge.id, "tooFast")
            return

        try:
            self.client.accept_challenge(challenge.id)
        except Exception as e:
            print(e)
