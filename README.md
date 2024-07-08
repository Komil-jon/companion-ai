# Flexible AI-Powered Text Genius
##########################################################

# Description
Using flask framework, g4f library for AI use, using local files / mongo database to store data and telegram open API to offer AI powered chat bot.

# Deployment
1. ## Clone/Fork this repository
2. ## Assets
   - Choose whether you want database approach or local files approach
   - Dpending on this use one of the two files of code
   - Create history and users collections in companion database in MongoDB
4. ## Environmental variables
   - ADMIN - your telegram ID
   - BOT_TOKEN - your telegram bot's API token
   - GROUP - telegram group ID that the bot can send generated message
   - USERNAME - mongodb username
   - PASSWORD - mongodb user password
   - GEMINI_API - gemini AI API token
   - STT_API - assembly AI API token to convert speech to text


# Future Plans
- *Making an efficient use of Gemini AI to process photos*
- *Offering a choice to give the output (text/audio)*
- *Implementing image generation/image enhancement*
- *Adding new free AI tools*
