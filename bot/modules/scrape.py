from telegram.ext import CommandHandler
from bot import AUTHORIZED_CHATS, dispatcher
from bot.helper.ext_utils.bot_utils import new_thread
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage
from bot.helper.ext_utils.parser import get_gp_link, appdrive_dl

@new_thread
def scraper_cmd(update, context):
    try:
       query = update.message.text.split()[1]
    except:
       sendMessage('<b>Give a GPlink or AppDrive link along with this command! 👀</b>', context.bot, update.message)
       return
 
    if query.startswith("https://gplinks"):        
       m = sendMessage('<b>Please wait...</b>', context.bot, update.message)
       link = get_gp_link(query)
    elif query.startswith("https://appdrive"):
       m = sendMessage('<b>Please wait...</b>', context.bot, update.message)
       l = appdrive_dl(query)
       link = l['gdrive_link']
    else:
       sendMessage('<b>Sorry, all I do is scrape GPLinks & AppDrive :(</b>', context.bot, update.message)
       return
 
    deleteMessage(context.bot, m)
    if not link:      
       sendMessage("Something went wrong\nTry again later..", context.bot, update.message)
    else:
       sendMessage(f"<b>Here is your link:\n\n{link}</b>", context.bot, update.message)
    

    
scrapper_handler = CommandHandler("scrape", scraper_cmd,
                               filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(scrapper_handler)
