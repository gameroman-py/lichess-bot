import os
import threading
import logging
from requests import HTTPError

from lichess import LichessClient, schemas
from lichess.custom import BotGameStreamEvent

from stockfish import Stockfish  # type: ignore


SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)

STOCKFISH_PATH = os.path.join(BASE_DIR, "stockfish", "stockfish.exe")


logger = logging.getLogger(__name__)


class Game(threading.Thread):
    def __init__(self, client: LichessClient, game: schemas.GameEventInfo):
        super().__init__()

        self.client = client
        self.game = game
        self.id = game.id

        self.stockfish = Stockfish(path=STOCKFISH_PATH)

    def run(self):
        self.handle_run()

        event_stream = self.client.stream_bot_game_state(self.game.id)
        for event in event_stream:
            try:
                self.handle_game_event(event)
            except HTTPError as e:
                logging.exception(
                    f"HTTPError Error in handle_game_event (error code: {e.response.status_code})"
                )

    def handle_run(self):
        if self.game.isMyTurn:
            self.stockfish.set_fen_position(self.game.fen)
            move = self.stockfish.get_best_move_time(150)
            assert move, "Best move not found"
            logger.info(f"Making first move: {move}")
            self.client.make_bot_move(self.id, move)

    def handle_game_event(self, event: BotGameStreamEvent):
        logger.info(f"Bot game event: {event.type}")
        match event.type:
            case "gameState":
                self.handle_game_state_event(event)
            case _:
                pass

    def post_message(self, message: str, spectator: bool = False):
        self.client.bot_write_game_chat_message(
            self.id, ("spectator" if spectator else "player"), message
        )

    def handle_game_state_event(self, game_state: schemas.GameStateEvent):
        logger.info(f"Game state: {game_state.status}")
        match game_state.status:
            case "started":
                self.handle_game_position(game_state)
            case _:
                pass

    def handle_game_position(self, game_state: schemas.GameStateEvent):
        moves = game_state.moves.split()
        self.stockfish.set_fen_position(self.game.fen)
        self.stockfish.make_moves_from_current_position(moves)

        move_count = len(moves)

        is_white_turn = move_count % 2 == 0

        turn = "white" if is_white_turn else "black"

        if turn != self.game.color:
            return  # Not our turn

        time_remaining = game_state.wtime if self.game.color == "white" else game_state.btime
        time_bonus = game_state.winc if self.game.color == "white" else game_state.binc

        logger.info(f"Time remaining: {time_remaining}. Time bonus: {time_bonus}")

        time_to_think = min(max(0, time_bonus - 100) + time_remaining // 300, 60 * 1000)

        move = self.stockfish.get_best_move_time(time_to_think)

        assert move, "Best move not found"

        logger.info(f"Making move: {move}")

        self.client.make_bot_move(self.id, move)
