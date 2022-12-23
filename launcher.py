import json
from typing import Any

from bot import OddBot
from cogs.utils.database import Database


def load_config() -> dict[str, Any]:
    with open("config.json", "r") as f:
        config = json.load(f)

    return config


def main() -> None:
    db = Database(load_config())
    bot = OddBot(
        config=load_config(),
        cmd_prefix="ob.",
        db=db
    )
    bot.run(bot.config["discord_api_token"])


if __name__ == '__main__':
    main()
    