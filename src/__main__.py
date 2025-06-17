import os
import logging

from dotenv import load_dotenv
from Computer import Computer


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

    load_dotenv(dotenv_path=ENV_FILE_PATH)

    LICHESS_BOT_TOKEN = os.getenv("LICHESS_BOT_TOKEN")
    if not LICHESS_BOT_TOKEN:
        raise ValueError("LICHESS_BOT_TOKEN is missing in .env")

    computer = Computer(LICHESS_BOT_TOKEN)

    try:
        logging.info("Starting the bot...")
        computer.run()

    except KeyboardInterrupt:
        logger.info("[KeyboardInterrupt] Stopping the bot...")


if __name__ == "__main__":
    main()
