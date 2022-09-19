from bot import Bot


def main():
    bot = Bot()
    bot.run(bot.config.DISCORD_API_TOKEN)


if __name__ == '__main__':
    main()