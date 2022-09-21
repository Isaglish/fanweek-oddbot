from bot import Bot


def main() -> None:
    bot = Bot()
    bot.run(bot.config["discord_api_token"])


if __name__ == '__main__':
    main()