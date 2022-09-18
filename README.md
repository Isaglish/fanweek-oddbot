# Odd Bot
![GitHub](https://img.shields.io/github/license/Isaglish/oddbot)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/Isaglish/oddbot/main)

A personal project made for the Fanweek event discord server.

## Note
I don't intend on making Odd Bot a public bot that can be used by anyone as I don't find any reason to do so. It's not like everyone has a Fancade related server that could use Odd Bot, plus there is not a lot of unique features I can provide and there are lots of bots out there that already does most stuff for you.

However, this source is provided to give you an idea on how I created Odd Bot and probably help you on developing your own.

## Features

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
    > You need Manage Server permission to unsubmit another `[member]`'s submission.
    
    - **`/submissions show [member: None] [all: False]`**
    
    > Shows all of your submissions
    >
    > Shows all of `[member]`'s submissions
    >
    > Shows `[all]` (everyone)'s submissions
    
### Context Menus

- **Report User**

    > Sends you a form to fill out for reporting.
    
    
## License
[MIT](https://github.com/Isaglish/oddbot/blob/main/LICENSE)