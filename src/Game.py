import os
import threading
import logging

from lichess import LichessClient
from lichess import schemas

from stockfish import Stockfish

from event_types import BotGameEvent


SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)

STOCKFISH_PATH = os.path.join(BASE_DIR, "stockfish", "stockfish.exe")

logger = logging.getLogger(__name__)


class Game(threading.Thread):
    def __init__(self, client: LichessClient, game: schemas.GameEventInfo, **kwargs):
        super().__init__(**kwargs)

        self.client = client
        self.game = game
        self.playing_as = game.color
        self.id = game.id

        self.stockfish = Stockfish(path=STOCKFISH_PATH)

    def run(self):
        logger.info(f"New game started: {self.game.id}")
        if self.game.isMyTurn:
            self.stockfish.set_fen_position(self.game.fen)
            move = self.stockfish.get_best_move_time(150)
            if move is None:
                logger.error("Best move not found")
                return
            logger.info(f"Making first move: {move}")
            self.client.make_bot_move(self.id, move)

        event_stream = self.client.stream_bot_game_state(self.game.id)
        for event in event_stream:
            if event is None:
                continue
            self.handle_game_event(event)

    def handle_game_event(self, event: BotGameEvent):
        logger.info(f"Bot game event: {event.type}")
        match event.type:
            case "gameState":
                self.handle_game_state_event(event)
            case "chatLine":
                self.handle_chat_line(event)

    def post_message(self, message: str, spectator=False):
        self.client.bot_write_game_chat_message(
            self.id, ("spectator" if spectator else "player"), message
        )

    def handle_game_state_event(self, game_state: schemas.GameStateEvent):
        logger.info(f"Game state: {game_state.status}")
        match game_state.status:
            case "started":
                try:
                    self.stockfish.set_fen_position(self.game.fen)
                    moves = game_state.moves.split()
                    self.stockfish.set_position(moves)
                    move = self.stockfish.get_best_move_time(700)
                    if move is None:
                        logger.error("Best move not found")
                        return
                    logger.info(f"Making move: {move}")
                    try:
                        self.client.make_bot_move(self.id, move)
                    except Exception as e:
                        logger.error(f"Failed to make a move: {e}")
                except Exception as e:
                    logger.exception(f"Error handling game state event: {e}")

            case "aborted":
                self.post_message("You dont want to play with me?\nMaybe we will play next time")

            case "draw" | "stalemate":
                self.post_message("This is a draw")

            case "outoftime":
                if game_state.winner == self.playing_as:
                    self.post_message("You lost on time! I won!")
                else:
                    self.post_message("Oh no! I lost on time!")

            case "resign":
                if game_state.winner == self.playing_as:
                    self.post_message("You resigned! I won!")
                else:
                    self.post_message("Oh no! Why did I resign?")

            case "mate":
                if game_state.winner == self.playing_as:
                    self.post_message("Yes! I checkmated you!")
                else:
                    self.post_message("Oh no! You checkmated me!")

    def handle_chat_line(self, chat_line: schemas.ChatLineEvent):
        if chat_line.username == "GameRoManBot":
            return
        if chat_line.room != "player":
            return
        if chat_line.username == "lichess":
            self.post_message("I cannot accept draw")
        else:
            self.post_message(chat_line.text)
