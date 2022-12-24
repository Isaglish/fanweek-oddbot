import json
from typing import Any

from bot import OddBot


def load_config() -> dict[str, Any]:
    with open("config.json", "r") as f:
        config = json.load(f)

    return config


def main() -> None:
    bot = OddBot(
        config=load_config(),
        cmd_prefix="ob."
    )
    bot.run(bot.config["discord_api_token"])


if __name__ == '__main__':
    main()
    