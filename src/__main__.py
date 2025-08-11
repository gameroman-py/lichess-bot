import os
import logging

from dotenv import load_dotenv
from Computer import Computer


def load_env(ENV_FILE_PATH: str):
    load_dotenv(dotenv_path=ENV_FILE_PATH)

    LICHESS_BOT_TOKEN = os.getenv("LICHESS_BOT_TOKEN")
    if not LICHESS_BOT_TOKEN:
        raise ValueError("LICHESS_BOT_TOKEN is missing in .env")

    STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")
    if not STOCKFISH_PATH:
        raise ValueError("STOCKFISH_PATH is missing in .env")

    return LICHESS_BOT_TOKEN, STOCKFISH_PATH


def main():
    SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(SRC_DIR)

    LOG_FILE_PATH = os.path.join(BASE_DIR, "logs", "app.log")
    ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")],
    )

    logger = logging.getLogger(__name__)

    LICHESS_BOT_TOKEN, STOCKFISH_PATH = load_env(ENV_FILE_PATH)

    computer = Computer(LICHESS_BOT_TOKEN, STOCKFISH_PATH)

    try:
        logging.info("Starting the bot...")
        computer.run()

    except KeyboardInterrupt:
        logger.info("[KeyboardInterrupt] Stopping the bot...")

    except Exception as e:
        logger.exception(f"[Exception] {e}")
        raise Exception from e


if __name__ == "__main__":
    main()
