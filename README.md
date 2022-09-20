# Odd Bot
[![GitHub](https://img.shields.io/github/license/Isaglish/fanweek-oddbot?style=flat-square)](https://github.com/Isaglish/fanweek-oddbot/blob/main/LICENSE)
[![GitHub last commit (branch)](https://img.shields.io/github/last-commit/Isaglish/fanweek-oddbot/main)](https://github.com/Isaglish/fanweek-oddbot/commits)
[![GitHub issues](https://img.shields.io/github/issues-raw/Isaglish/fanweek-oddbot)](https://github.com/Isaglish/fanweek-oddbot/issues)
[![Discord](https://img.shields.io/discord/758487559399145524?color=%235865F2&label=discord&logo=discord&logoColor=white)](https://discord.gg/XRTQbZJ)

A personal project made for the Fanweek event discord server.

## Note
I don't intend on making Odd Bot a public bot that can be used by anyone as I don't find any reason to do so. It's not like everyone has a Fancade related server that could use Odd Bot, plus there is not a lot of unique features I can provide and there are lots of bots out there that already does most stuff for you.

However, this source is provided to give you an idea on how I created Odd Bot and probably help you on developing your own.

## Table of Contents

- [Features](#features)
    - [Text Commands](#text-commands)
    - [Slash Commands](#slash-commands)
        - [Submissions](#submissions)
    - [Context Menus](#context-menus)
- [Issues](#issues)
- [Links](#links)

## Features

### Text Commands

- **`ob.source`**

    > Returns the link to this repository

- **`ob.help`**

    > Returns a link to the Features section of this README

### Slash Commands

Parameters inside `<>` are required.

Parameters inside `[default: value]` are optional.

- ### Submissions
    - **`/submissions submit <link> [member: None]`**
    
        > Saves your submission into the database.
        >
        > You need Manage Server permission to submit for `[member]`.
    
    - **`/submissions unsubmit <link>`**
    
        > Removes your submission from the database.
        >
        > You need Manage Server permission to unsubmit another member's submission.
    
    - **`/submissions show [member: None] [all: False]`**
    
        > Shows all of your submissions.
        >
        > Shows all of `[member]`'s submissions.
        >
        > `[all]` shows everyone's submissions.

    - **`/submissions clear [member: None] [all: False]`**

        > Clears all of your submissions.
        >
        > You need Manage Server permission to clear another member's submissions.
        >
        > Clears all of `[member]`'s submissions.
        >
        > `[all]` clears everyone's submissions.
    
- ### Context Menus

    - **Report User**

        > Sends you a form to fill out for reporting.

## Issues
If you find any bugs, issues, or unexpected behaviour while using the bot, you should open an issue with details of the problem and how to reproduce if possible. Please also open an issue for any new features or commands you would like to see added.
    
## Links
- **License:** [MIT](https://github.com/Isaglish/fanweek-oddbot/blob/main/LICENSE)
- **Repository:** [GitHub](https://github.com/Isaglish/fanweek-oddbot)