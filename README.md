# CyberBus2
CyberBus2 (codenamed Umi, currently powering Ricky#6849 on the NeoZones Discord server) is a spiritual successor to [the original NeoZones CyberBus bot.](https://github.com/NeoZones/CyberBus)

## Concepts you should know
CyberBus2 is written in Python (3.10+) and makes use of the Pycord library (latest commits from the master branch, v2.0 rewrite pre-release). It is therefore considered bleeding-edge.

Within Pycord, you should be aware of the following concepts:

- A **Client** is an abstraction used by Pycord to connect to Discord given a token and some actions to perform.
- A **Bot** is a more specific abstraction used by Pycord to support commands and listeners. For most targeted use cases, Bots should be used instead of Clients.
- A **Cog** is a class that can be used to organize and self-contain related commands and functionality. Cogs can be loaded and unloaded into a Bot or Client.
- An **Extension** is an external file that can be loaded by a main script. Extensions contain a `setup()` function which can be used to prepare a Bot or Client for operation. Generally, this is used to add the external Cog to the Bot or Client.

Within Python, you should be aware of the following concepts:

- **asyncio**: Pycord is built on *coroutines* which can be executed *asynchronously*; in other words, there is an event loop which processes events not necessarily in the order you write them or call them in your code. This is denoted by the use of `async` before functions, and `await` before coroutines within those functions. Essentially, you should 
- **Classes**: Just like it is possible to write your code all in one file, it is also possible to leave all your code running in one context. However, the use of classes (and separate files) can be used to better organize your code and better understand what each self-contained section of it will do. When using classes, the `__init__()` function will initialize each instance of the Class. Because of this, it requires a `self` parameter, and consequently, all functions within that class will also require a `self` parameter. This parameter is implied, meaning it does not have to be explicitly passed into function calls; instead, `self` must be used as a prefix in order to reference the function contained within the instance of the Class object. For example, if you write a function with `def function(self)`, you would call it elsewhere with `self.function()` instead of with `function(self)`. Any additional parameters can be passed in like normal.
- **Decorators**: Decorators are essentially statements which wrap functions in other functions. Pycord uses decorators to define user/message/application commands, as well as event listeners. if no name is provided as a parameter within that decorator, Pycord will default to using the function name for that command or listener.

## Architectural breakdown

The main script used to run this application is found in the root of the repository at `app.py`.

Extensions are loaded from the `cogs/` folder. Currently, the following cogs are provided:

- **immigration**: When a Discord profile joins or leaves the guild, send a message to a specified logging channel. Also record bans and unbans. This cog uses listeners for `on_member_join`, `on_member_remove`, `on_member_ban`, and `on_member_unban`.
- **music**: Plays requested URLs, files, and other queries within a voice channel. If a query does not correspond to a URL, local file, or attachment, then the bot will perform a YouTube search for the given query. Local files are stored in the `sounds/normalized` directory, and the `normalize` bash script in `sounds/` can be used to automatically normalize any audio files placed in `sounds/originals`. This cog uses message commands.
- **piss**: Provide too much information when a certain substance is mentioned. This cog uses listeners for `on_message`.
- **random**: Use random.org's old HTTP API to provide truly random results. Supports rolling dice and flipping coins. This cog uses message commands.
- **roles**: Allow members to self-assign roles by reacting or unreacting to a specified message. Also provides an application command to set a color role. This cog uses listeners for `on_raw_reaction_add` and `on_raw_reaction_remove`, and it also uses message commands and application commands.
- **sus**: Reacts with a custom emoji `:trash:` when any reference to Among Us is made. This cog uses listeners for `on_message`.
- **uwu**: Take some text and uwu-ify it. This cog uses message commands.

Some utility scripts are provided to interface with the Discord REST API. These scripts can be found in the `utils/` folder. Currently, the following scripts are provided:

- **post.py**: Create a post within a specified channel.
- **react.py**: React with an emoji to a specified post within a specified channel. Emoji must be URL-encoded.'
- **username.py**: Change your bot user's username, since this cannot currently be done from the Discord developer dashboard.

For use with the music cog, a `sounds/` directory is provided.
- Sound files may be placed in the `sounds/originals` subdirectory, and additional subdirectories are supported.
- The `normalize` Bash script should be used to normalize all audio within the `originals` subdirectory.
- The bot will check for sound files within the `sounds/normalized` subdirectory, which is where the `normalize` script will output all of its files.

## Getting started

### Pre-requisites
- Python 3.10+
- ffmpeg
- youtube-dl

### Instructions

1. Clone this repo somewhere: `git clone <url>`
2. Change into the directory: `cd CyberBus2`
3. Fetch the pycord repo: `git submodule update --init`
4. (Optional, but recommended) Create a virtual environment to install dependencies: `virtualenv .venv`
5. (If you performed the above step) Activate the virtual environment: `source .venv/bin/activate`
6. Create a .env file with `BOT_TOKEN = <insert your token here>`
7. Run the app with `python app.py`

### Modifications you may want to make if you want to use this code to power your bot
Currently, the following are hardcoded:
- cogs/immigration.py
  - The channel to post member joins/leaves/bans/unbans should be changed
  - The actual messages to send can be edited as well, if you wish
- cogs/music.py
  - There is a function to check for permission before using `play` or `playtop`, which can be removed or modified
  - The actual messages to send can be edited as well, if you wish
- cogs/roles.py
  - All roles are currently defined in a dictionary called `roles`, where a role can be of type `COLOR_`, `PING_`, or `PRONOUN_` -- this can be changed, but make sure to change the `/color` application command if you do so
  - All messages to be reacted to are also hardcoded by ID within `if` statements
  - Guild ID is hardcoded within the `/color` application command's decorator
- cogs/sus.py
  - The emoji to react with is hardcoded to a certain custom emoji, so it should be edited
