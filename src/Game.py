import threading

from lichess import LichessClient
from lichess import schemas

from stockfish import Stockfish


STOCKFISH_PATH = "stockfish"


class Game(threading.Thread):
    def __init__(self, client: LichessClient, game: schemas.GameEventInfo, **kwargs):
        super().__init__(**kwargs)

        self.fen = game.fen
        self.playing_as = game.color
        self.isMyTurn = game.isMyTurn
        self.id = game.id
        self.client = client
        self.stream = client.stream_bot_game_state(game.id)
        self.stockfish = Stockfish(path=STOCKFISH_PATH)

    def run(self):
        if self.isMyTurn:
            self.stockfish.set_fen_position(self.fen)
            move = self.stockfish.get_best_move_time(150)
            if move is None:
                raise Exception("Best move not found")
            self.client.make_bot_move(self.id, move)

        for event in self.stream:
            if event is None:
                continue
            match event.type:
                case "gameState":
                    self.handle_state_change(event)
                case "chatLine":
                    self.handle_chat_line(event)

    def post_message(self, message: str, spectator=False):
        self.client.bot_write_game_chat_message(self.id, ("spectator" if spectator else "player"), message)

    def handle_state_change(self, game_state: schemas.GameStateEvent):
        match game_state.status:
            case "started":
                try:
                    self.stockfish.set_fen_position(
                        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                    )
                    moves = game_state.moves.split()
                    self.stockfish.set_position(moves)
                    move = self.stockfish.get_best_move_time(700)
                    if move is None:
                        raise Exception("move not found")
                    self.client.make_bot_move(self.id, move)

                except Exception as e:
                    print(e)

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
