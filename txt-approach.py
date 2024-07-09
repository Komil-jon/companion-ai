import io
import os
import g4f
import time
import json
import base64
import requests
import PIL.Image
import urllib.request
import assemblyai as aai
from flask import Flask, request
import google.generativeai as genai

#global last_update_id
# only for testing


BOT_TOKEN = os.getenv('BOT_TOKEN')
GIT_TOKEN = os.getenv('GIT_TOKEN')
ADMIN = os.getenv('ADMIN')
GROUP = os.getenv('GROUP')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
GEMINI_API = os.getenv('GEMINI_API')
STT_API = os.getenv('STT_API')

MODELS = [{'name': 'Mixtral','description': 'a chatbot that can provide helpful responses and assist with various tasks including finding information, generating text, crawling the web, answering questions, and more\\.','instruction': 'be a helpful assistant. You are Bing AI.','model': 'mixtral-8x7b','provider': g4f.Provider.DeepInfra},
          {'name': 'Blackbox','description': 'a chatbot that can provide helpful responses and assist with various tasks including finding information, generating text, crawling the web, answering questions, and more\\.','instruction': 'be a helpful assistant. You are Bing AI.', 'model': 'blackbox','provider': g4f.Provider.DeepInfra},
          {'name': 'Commander','description': 'a chatbot that can provide helpful responses and assist with various tasks including finding information, generating text, crawling the web, answering questions, and more\\.','instruction': 'be a helpful assistant. You are Oculus AI.','model': 'command-r+', 'provider': g4f.Provider.Koala},]
MODEL = ["Mixtral", "Blackbox", "Commander"]
REACTIONS = {'Mixtral': '⚡️', 'Blackbox': '👨‍💻', 'Commander': '🔥'}

app = Flask(__name__)
genai.configure(api_key=GEMINI_API)
aai.settings.api_key = STT_API


@app.route('/', methods=['POST'])
def handle_webhook():
    try:
        process(json.loads(request.get_data()))
        return 'Success!'
    except Exception as e:
        print(e)
        return 'Error'
              
@app.route('/activate', methods=['GET'])
def activate():
    return "Activation successful!", 200
          
def testing():
    global last_update_id
    last_update_id = -1
    while True:
        updates = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id}").json().get('result', [])
        for update in updates:
            process(update)
            last_update_id = update['update_id'] + 1

def process(update):
    if 'message' in update:
        if 'text' in update['message']:
            message = update['message']['text']
            if message == '/start':
                if not any(str(update['message']['from']['id']) in line.split()[0] for line in open('users.txt')):
                    open('users.txt', 'a').write(f"{update['message']['from']['id']} {update['message']['from']['first_name'].split()[0]}\n")
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={'chat_id': update['message']['from']['id'],'text': f"✅ Hello <a href='tg://user?id={update['message']['from']['id']}'>{update['message']['from']['first_name']}</a> !",'parse_mode': 'HTML'})
                    alert(update['message']['from'])
                    git_update("users.txt")
                open(f"{update['message']['from']['id']}.txt", 'w').write(MODELS[0]['name'])
                menu(update['message']['from']['id'])
            elif message == '/new_chat':
                if os.path.exists(f"{update['message']['from']['id']}.json"):
                    os.remove(f"{update['message']['from']['id']}.json")
                menu(update['message']['from']['id'])
            elif message == '/credits':
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={'chat_id': update['message']['from']['id'],'text': "*Special shoutout to:*\n\n- *Google's Gemini API* _for enabling natural language understanding and generation._\n\n- *Meta's Llama API* _for providing advanced language model capabilities._\n\n- *DeepInfra's OpenAI Models* _for contributing to the bot's text comprehension and generation._\n\n*And a big thanks to the Telegram Community for their support and feedback!*\n\n*Lead Developer:* _Komiljon Qosimov_ @boot2root\n\n*We appreciate everyone's contributions to this Telegram bot. Your work has brought AI-driven communication to Telegram users.*",'parse_mode': 'Markdown'})
            elif message == '/info':
                text = "__Here are brief overview of each AI model 💁🏼‍♂️__\n\n"
                for item in MODELS:
                    text += f"*🤖 {item['name']}: *_{item['description']}_\n\n"
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={'chat_id': update['message']['from']['id'],'text': text,'parse_mode': 'MarkdownV2'}).json()
            elif message == '/INITIALIZE' and update['message']['from']['id'] == ADMIN:
                initialize()
            elif message == '/USERS' and update['message']['from']['id'] == ADMIN:
                send_users()
            elif 'reply_to_message' in update['message'] and 'photo' in update['message']['reply_to_message']:
                photo(update['message']['from']['id'], update['message']['message_id'], update['message']['text'], requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile', params={'file_id': update['message']['reply_to_message']['photo'][3]['file_id']}).json()['result']['file_path'])
            else:
                try:
                    model = open(f"{update['message']['from']['id']}.txt", 'r').read()
                except:
                    model = MODEL[0]
                if model == ' ':
                    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',json={'chat_id': update['message']['from']['id'],'text': f'*Please choose one AI model*\n_List of available assistants should be pinned_','parse_mode': 'Markdown','reply_to_message_id': update['message']['message_id']})
                    return
                reply_markup = {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]}
                edit_id = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',json={'chat_id': update['message']['from']['id'],'text': f'*✅ {model}* _is generating..._', 'reply_markup': reply_markup,'parse_mode': 'Markdown','reply_to_message_id': update['message']['message_id']}).json()['result'][
                    'message_id']
                initial(update['message']['from']['id'], update['message']['text'], model, edit_id)
        elif 'voice' in update['message']:
            try:
                model = open(f"{update['message']['from']['id']}.txt", 'r').read()
            except:
                model = MODELS[0]['name']
            try:
                reply_markup = {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]}
                edit_id = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                                        json={'chat_id': update['message']['from']['id'],
                                              'text': f"🧏🏻‍♂️ _Your voice is being processed_",
                                              'reply_markup': reply_markup, 'parse_mode': 'Markdown',
                                              'reply_to_message_id': update['message']['message_id']}).json()['result'][
                    'message_id']
                initial(update['message']['from']['id'], stt(
                    requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile',
                                 params={'file_id': update['message']['voice']['file_id']}).json()['result'][
                        'file_path']), model, edit_id, )
            except Exception as e:
                requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',
                              json={'chat_id': update['message']['from']['id'], 'message_id': edit_id,
                                    'text': f'_Sorry, I could not catch you_', 'parse_mode': 'Markdown',
                                   'reply_to_message_id': update['message']['message_id']})
        elif 'photo' in update['message']:
            if 'caption' in update['message']['photo']:
                photo(update['message']['from']['id'], update['message']['message_id'], update['message']['photo']['caption'], requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile', params={'file_id': update['message']['photo'][-1]['file_id']}).json()['result']['file_path'])
            else:
                photo(update['message']['from']['id'], update['message']['message_id'], '', requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile', params={'file_id': update['message']['photo'][-1]['file_id']}).json()['result']['file_path'])
        elif 'pinned_message' in update['message']:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",json={'chat_id': update['message']['chat']['id'], 'message_id': update['message']['message_id']})
    elif 'callback_query' in update and 'data' in update['callback_query']:
        data = update['callback_query']['data']
        if data in MODEL:
            for item in MODELS:
                if item['name'] == data:
                    json.dump([{"role": "system", "content": item['instruction']}], open(f"{update['callback_query']['from']['id']}.json", 'w'), indent=4)
            print(requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",json={'callback_query_id': update['callback_query']['id'],'text': """I hope you understand that:\n\n1. AI responses may be inaccurate or inappropriate.\n2. AI's responses may lack guarantees and show bias.\n3. Use AI responsibly, improper use may lead to termination.""", 'show_alert': True}).json())
            options(update['callback_query']['from']['id'], data, update['callback_query']['message']['message_id'])
        elif data[0] == 'R':
            reply_markup = update['callback_query']['message']['reply_markup']
            if len(update['callback_query']['message']['reply_markup']['inline_keyboard'][1]) >= 5:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",json={'callback_query_id': update['callback_query']['id'], 'text': 'You can not generate more than 5 drafts!'})
                reply_markup['inline_keyboard'][0] = [
                    {'text': 'You have reached the limit 😔', 'callback_data': 'limit'}]
                print(requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageReplyMarkup',
                                    json={'chat_id': update['callback_query']['from']['id'],
                                          'message_id': update['callback_query']['message']['message_id'],
                                          'reply_markup': json.dumps(reply_markup)}).json())
                return
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",json={'callback_query_id': update['callback_query']['id'],'text': 'Generating...'})
            for index, button in enumerate(reply_markup['inline_keyboard'][1]):
                if button['text'] == '🙄':
                    button['text'] = f"Draft {index + 1}"
            if 'voice' in update['callback_query']['message']['reply_to_message']:
                reply_markup['inline_keyboard'][0] = [{'text': "Delete ❌", 'callback_data': f"delete"}]
                requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',
                              json={'chat_id': update['callback_query']['from']['id'],
                                    'text': f"🧏🏻‍♂️ _Your voice is being processed_",
                                    'message_id': update['callback_query']['message']['message_id'],
                                    'parse_mode': 'Markdown', 'reply_markup': json.dumps(reply_markup)}).json()
                core(update['callback_query']['from']['id'], update['callback_query']['message']['message_id'], stt(
                    requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile', params={
                        'file_id': update['callback_query']['message']['reply_to_message']['voice']['file_id']}).json()[
                        'result']['file_path']), data.split()[1],
                     len(update['callback_query']['message']['reply_markup']['inline_keyboard'][1]), reply_markup)
            elif 'text' in update['callback_query']['message']['reply_to_message']:
                core(update['callback_query']['from']['id'], update['callback_query']['message']['message_id'],
                     update['callback_query']['message']['reply_to_message']['text'], data.split()[1],
                     len(update['callback_query']['message']['reply_markup']['inline_keyboard'][1]), reply_markup)
        elif data[0] == 'D':
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",json={'callback_query_id': update['callback_query']['id'],'text': 'Sending...'})
            reply_markup = update['callback_query']['message']['reply_markup']
            for index, button in enumerate(reply_markup['inline_keyboard'][1]):
                if button['text'] == '🙄':
                    button['text'] = f"Draft {index + 1}"
            reply_markup['inline_keyboard'][1][int(data.split()[2]) - 1]['text'] = '🙄'
            if requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/copyMessage',data={'chat_id': update['callback_query']['from']['id'], 'parse_mode': 'Markdown', 'from_chat_id': GROUP,'message_id': int(data.split()[1]), 'reply_markup': json.dumps(reply_markup),'reply_to_message_id': update['callback_query']['message']['reply_to_message']['message_id']}).status_code != 200:
                requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/copyMessage',data={'chat_id': update['callback_query']['from']['id'], 'from_chat_id': GROUP,'message_id': int(data.split()[1]), 'reply_markup': json.dumps(reply_markup),'reply_to_message_id': update['callback_query']['message']['reply_to_message']['message_id']})
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
                          json={'chat_id': update['callback_query']['from']['id'],
                                'message_id': update['callback_query']['message']['message_id']})
        elif data == 'limit':
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",json={'callback_query_id': update['callback_query']['id'],'text': 'You can not generate more than 5 drafts!'})
            params = {'chat_id': update['callback_query']['from']['id'],'message_id': update['callback_query']['message']['message_id'], 'is_big': True,'reaction': json.dumps([{'type': 'emoji', 'emoji': '😢'}])}
            requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction', params=params).json()
        elif data == 'delete':
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",json={'callback_query_id': update['callback_query']['id'],'text': 'Deleting...'})
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",json={'chat_id': update['callback_query']['from']['id'],'message_id': update['callback_query']['message']['message_id']})

def menu(user_id):
    open(f'{user_id}.txt', 'w').write(' ')
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction",json={'chat_id': user_id, 'action': 'choose_sticker'})
    reply_markup = {'inline_keyboard': []}
    if len(MODEL) % 2 == 0:
        for i in range(0, len(MODEL), 2):
            reply_markup['inline_keyboard'].append([{'text': f"{MODEL[i]}", 'callback_data': f"{MODEL[i]}"},
                                                    {'text': f"{MODEL[i + 1]}", 'callback_data': f"{MODEL[i + 1]}"}])
    else:
        for i in range(0, len(MODEL) - 1, 2):
            reply_markup['inline_keyboard'].append([{'text': f"{MODEL[i]}", 'callback_data': f"{MODEL[i]}"},
                                                    {'text': f"{MODEL[i + 1]}", 'callback_data': f"{MODEL[i + 1]}"}])
        reply_markup['inline_keyboard'].append([{'text': f"{MODEL[-1]}", 'callback_data': f"{MODEL[-1]}"}])
    message_id = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
                               params={'chat_id': user_id, 'text': f"*Choose your default AI assistant:*",
                                       'parse_mode': 'Markdown', 'reply_markup': json.dumps(reply_markup)}).json()[
        'result']['message_id']
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction',
                  params={'chat_id': user_id, 'message_id': message_id, 'is_big': True,
                          'reaction': json.dumps([{'type': 'emoji', 'emoji': f"🙏"}])})
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/unpinAllChatMessages',params={'chat_id': user_id})
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/pinChatMessage', params={'chat_id': user_id, 'message_id': message_id}).json()

def options(user_id, data, message_id):
    open(f"{user_id}.txt", 'w').write(data)
    reply_markup = {'inline_keyboard': []}
    if len(MODEL) % 2 == 0:
        for i in range(0, len(MODEL), 2):
            if data == MODEL[i]:
                reply_markup['inline_keyboard'].append(
                    [{'text': f"{MODEL[i]} {REACTIONS[MODEL[i]]}", 'callback_data': f"{MODEL[i]}"},
                     {'text': f"{MODEL[i + 1]}",
                      'callback_data': f"{MODEL[i + 1]}"}])
            elif data == MODEL[i + 1]:
                reply_markup['inline_keyboard'].append([{'text': f"{MODEL[i]}", 'callback_data': f"{MODEL[i]}"},
                                                        {'text': f"{MODEL[i + 1]} {REACTIONS[MODEL[i + 1]]}",
                                                         'callback_data': f"{MODEL[i + 1]}"}])
            else:
                reply_markup['inline_keyboard'].append([{'text': f"{MODEL[i]}", 'callback_data': f"{MODEL[i]}"},
                                                        {'text': f"{MODEL[i + 1]}",
                                                         'callback_data': f"{MODEL[i + 1]}"}])
    else:
        for i in range(0, len(MODEL) - 1, 2):
            if data == MODEL[i]:
                reply_markup['inline_keyboard'].append(
                    [{'text': f"{MODEL[i]} {REACTIONS[MODEL[i]]}", 'callback_data': f"{MODEL[i]}"},
                     {'text': f"{MODEL[i + 1]}",
                      'callback_data': f"{MODEL[i + 1]}"}])
            elif data == MODEL[i + 1]:
                reply_markup['inline_keyboard'].append([{'text': f"{MODEL[i]}", 'callback_data': f"{MODEL[i]}"},
                                                        {'text': f"{MODEL[i + 1]} {REACTIONS[MODEL[i + 1]]}",
                                                         'callback_data': f"{MODEL[i + 1]}"}])
            else:
                reply_markup['inline_keyboard'].append([{'text': f"{MODEL[i]}", 'callback_data': f"{MODEL[i]}"},
                                                        {'text': f"{MODEL[i + 1]}",
                                                         'callback_data': f"{MODEL[i + 1]}"}])
        if data == MODEL[-1]:
            reply_markup['inline_keyboard'].append([{'text': f"{MODEL[-1]} {REACTIONS[MODEL[-1]]}", 'callback_data': f"{MODEL[-1]}"}])
        else:
            reply_markup['inline_keyboard'].append([{'text': f"{MODEL[-1]}", 'callback_data': f"{MODEL[-1]}"}])
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id,'message_id': message_id, 'text': f'*You are chatting with* _{data}_\n','reply_markup': json.dumps(reply_markup), 'parse_mode': 'Markdown'})
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction',params={'chat_id': user_id, 'message_id': message_id, 'is_big': True,'reaction': json.dumps([{'type': 'emoji', 'emoji': REACTIONS[data]}])})

def initial(user_id, query, mode, edit_id):
    chat_history = json.load(open(f'{user_id}.json'))
    chat_history.append({"role": "user", "content": query})
    if mode == 'Gemini':
        try:
            response = genai.GenerativeModel('gemini-pro').generate_content(query).text
        except:
            response = "_I don't understand it. 🤔_"
    else:
        for item in MODELS:
            if item['name'] == mode:
                response = g4f.ChatCompletion.create(
                    model=item['model'],
                    messages=chat_history,
                    stream=True,
                )
                break
    output = ""
    start = time.time()
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction",json={'chat_id': user_id, 'action': 'typing'})
    for message in response:
        if isinstance(message, str):
            output += message
        if time.time() - start > 2:
            requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f'{output}', 'parse_mode': 'Markdown','message_id': edit_id, 'reply_markup': {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]}})
            start += 2
    chat_history.append({"role": "assistant", "content": output})
    with open(f'{user_id}.json', 'w') as file:
        json.dump(chat_history, file, indent=4)
    if requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': output + f'\n\n_Response by {mode}_', 'parse_mode': 'Markdown', 'message_id': edit_id,'reply_markup': {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]}}).status_code != 200:
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': output + f'\n\nResponse by {mode}', 'message_id': edit_id,'reply_markup': {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]}})
    copy_id = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/copyMessage',data={'chat_id': GROUP, 'from_chat_id': user_id, 'message_id': edit_id}).json()['result']['message_id']
    if len(chat_history) >= 11:
        extra = "Let's have a /new_chat"
    else:
        extra = f'{int(len(chat_history) / 2)}/5'
    if requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f'{output}\n\n_{extra}_', 'message_id': edit_id,'reply_markup': {'inline_keyboard': [[{'text': f"Regenerate ♻️", 'callback_data': f'R {mode}'},{'text': "Delete ❌", 'callback_data': f"delete"}], [{'text': f"Draft 1",'callback_data': f'D {copy_id} 1'}]]},'parse_mode': 'Markdown'}).status_code != 200:
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f'{output}\n\n<em>{extra}</em>','message_id': edit_id, 'reply_markup': {'inline_keyboard': [[{'text': f"Regenerate ♻️", 'callback_data': f'R {mode}'},{'text': "Delete ❌", 'callback_data': f"delete"}],[{'text': f"Draft 1", 'callback_data': f'D {copy_id} 1'}]]}, 'parse_mode': 'HTML'})

def core(user_id, message_id, query, mode, number,reply_markup):  # number can be obtained by iterating update['callback_query']['message']['reply_markup']['inline_keyboard'][1]
    chat_history = json.load(open(f'{user_id}.json'))
    chat_history.append({"role": "user", "content": query})
    if mode == 'Gemini':
        response = genai.GenerativeModel('gemini-pro').generate_content(query).text
    else:
        for item in MODELS:
            if item['name'] == mode:
                response = g4f.ChatCompletion.create(
                    model=item['model'],
                    messages=[{'role': 'user', 'content': query}, {'role': 'system', 'content': item['instruction']}],
                    stream=True,
                )
                break
    output = ""
    start = time.time()
    print(requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction",json={'chat_id': user_id, 'action': 'typing'}))
    reply_markup['inline_keyboard'][0] = [{'text': "Delete ❌", 'callback_data': f"delete"}]
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f'*✅ {mode}* _is generating..._', 'message_id': message_id,'reply_markup': reply_markup, 'parse_mode': 'Markdown'})
    for message in response:
        if isinstance(message, str):
            output += message
        if time.time() - start > 2:
            requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f'{output}', 'message_id': message_id,'reply_markup': reply_markup, 'parse_mode': 'Markdown'}).json()
            start += 2
    chat_history.append({"role": "assistant", "content": output})
    with open(f'{user_id}.json', 'w') as file:
        json.dump(chat_history, file, indent=4)
    if requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'parse_mode': 'Markdown', 'text': output + f'\n\n_Response by {mode}_', 'message_id': message_id, 'reply_markup': reply_markup}).status_code != 200:
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': output + f'\n\nResponse by {mode}', 'message_id': message_id, 'reply_markup': reply_markup})
    copy_id = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/copyMessage',data={'chat_id': GROUP, 'from_chat_id': user_id, 'message_id': message_id}).json()['result']['message_id']
    reply_markup['inline_keyboard'][1].append({'text': f"Draft {number + 1}", 'callback_data': f'D {copy_id} {number + 1}'})
    reply_markup['inline_keyboard'][0] = [{'text': f"Regenerate ♻️", 'callback_data': f'R {mode}'},{'text': "Delete ❌", 'callback_data': f"delete"}]
    if len(chat_history) >= 11:
        extra = "Let's have a /new_chat"
    else:
        extra = f'{int(len(chat_history) / 2)}/5'
    if requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f'{output}\n\n_{extra}_','message_id': message_id, 'reply_markup': reply_markup, 'parse_mode': 'Markdown'}).status_code != 200:
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f'{output}\n\n<em>{extra}</em>','message_id': message_id, 'reply_markup': reply_markup, 'parse_mode': 'HTML'})
def photo(user_id, message_id, query, file_url):
    # here we should warn that user is currently using gemini
    edit_id = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',json={'chat_id': user_id,'text': f'_✅ Currently only Gemini can respond to photos_', 'reply_markup': {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]},'parse_mode': 'Markdown','reply_to_message_id': message_id}).json()['result']['message_id']
    urllib.request.urlretrieve(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_url}", 'image.jpg')
    if query != '':
        img = PIL.Image.open('image.jpg')
        response = genai.GenerativeModel('gemini-pro-vision').generate_content([query,img], stream=True)
    else:
        img = PIL.Image.open('image.jpg')
        response = genai.GenerativeModel('gemini-pro-vision').generate_content(img, stream=True)
    response.resolve()
    #if os.path.exists('image.jpg'):
    #    os.remove('image.jpg')
    output = ""
    start = time.time()
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction",json={'chat_id': user_id, 'action': 'typing'})
    for message in response:
        output += message.text
        if time.time() - start > 2:
            requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f'{output}', 'parse_mode': 'Markdown','message_id': edit_id, 'reply_markup': {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]}})
            start += 2
    if requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f"{output}\n\n*Tip: *_Write what you want as a photo caption or as a reply message_", 'parse_mode': 'Markdown', 'message_id': edit_id,'reply_markup': {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]}}).status_code != 200:
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/editMessageText',json={'chat_id': user_id, 'text': f"{output}\n\n<strong>Tip: </strong><em>Write what you want as a photo caption or as a reply message</em>", 'message_id': edit_id,  'parse_mode': 'HTML', 'reply_markup': {'inline_keyboard': [[{'text': "Delete ❌", 'callback_data': f"delete"}]]}})

def image(user_id, message_id, query, format):
    payload = {
        "chat_id": user_id,
        "message_to_reply_id": message_id,
        "tetx": "*👨‍💻 This function will be available soon!*",
        "parse_mode": "Markdown"
    }
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
    return
    headers = {"Authorization": f"Bearer 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"}
    media = []
    for i in range(4):
        response = requests.post(GENERATION[i], headers=headers, json={"inputs": query})
        time.sleep(10)
        open('nano.jpeg', 'wb').write(response.content)
        try:
            media.append({"type": 'photo', "media":
                requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto', data={'chat_id': user_id},
                              files={'photo': open('nano.jpeg', 'rb')}).json()['result']['photo'][0]['file_id']})
        except:
            continue
    reply_markup = {'inline_keyboard': [
        [{'text': f"Neus AI ❤️‍🔥", 'callback_data': f"Neus"}, {'text': f"ChatGPT ❤️", 'callback_data': f"ChatGPT"}],
        [{'text': f"Mistral AI 💘", 'callback_data': f"Mistral"},
         {'text': f"HuggingFace AI 🔥", 'callback_data': f"HuggingFace"}],
        [{'text': f"Llama AI 🤩", 'callback_data': f"Llama"}],
        [{'text': f"Image Generator 👨‍💻", 'callback_data': f"IG"},
         {'text': f"Image Enhancer 🫡", 'callback_data': f"IE"}]
    ]}
    payload = {
        'chat_id': user_id,
        'message_id': message_id,
        'media': media,
        'quote': '*hello*',
        'quote_parse_mode': 'Markdown',
        "reply_markup": json.dumps(reply_markup)
    }
    edit_id = \
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMediaGroup", json=payload).json()['result'][0][
            'message_id']
    print(edit_id)
    payload = {
        "chat_id": user_id,
        "message_id": edit_id,
        'media': media,
        "reply_markup": json.dumps(reply_markup)
    }
    print(requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageReplyMarkup", json=payload).json())

def enhancer(user_id, message_id, query, format):
    payload = {
        "chat_id": user_id,
        "message_to_reply_id": message_id,
        "text": "*👨‍💻 This function will be available soon!*",
        "parse_mode": "Markdown"
    }
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)

def stt(file_url):
    return aai.Transcriber().transcribe(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_url}").text

def send_users():
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", params={'chat_id': ADMIN},files={'document': ('Users.txt', io.StringIO(''.join(open('users.txt', 'r').readlines())))})

def initialize():
    for line in open('users.txt', 'r').readlines():
        open(f'{line.split()[0]}.txt', 'w').write(' ')
def alert(user):
    params = {
        'chat_id': ADMIN,
        'text': "<strong>NEW MEMBER!!!\n</strong>" + json.dumps(user),
        'parse_mode': 'HTML',
    }
    requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', params=params)

def git_update(filename):
    username = "companionxbot"
    repository = "Copy"
    branch = "main"
    with open(filename, "r") as file:
        new_content = file.read()
    new_content_bytes = new_content.encode("utf-8")
    new_content_base64 = base64.b64encode(new_content_bytes).decode("utf-8")
    url = f"https://api.github.com/repos/{username}/{repository}/contents/{filename}"
    headers = {
        "Authorization": f"token {GIT_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()
    sha = response_data["sha"]
    payload = {
        "message": "Update users.txt",
        "content": new_content_base64,
        "sha": sha,
        "branch": branch
    }
    update_url = f"https://api.github.com/repos/{username}/{repository}/contents/{filename}"
    requests.put(update_url, json=payload, headers=headers)



if __name__ == '__main__':
    #testing()
    app.run(debug=False)
