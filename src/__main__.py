import os

from dotenv import load_dotenv

from Computer import Computer


load_dotenv()


def main():
    LICHESS_BOT_TOKEN = os.getenv("LICHESS_BOT_TOKEN")

    if not LICHESS_BOT_TOKEN:
        raise ValueError

    computer = Computer(LICHESS_BOT_TOKEN)
    computer.run()


if __name__ == "__main__":
    main()
