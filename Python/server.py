import os
import asyncio
import aiofiles
import openai
from pathlib import Path
import functools
import time
from datetime import datetime, timezone
import mimetypes
import re
import subprocess
import urllib.parse
import yaml
from urllib.parse import quote

from data import DataManager

data = DataManager("gopher.db")

# Helpful info: https://datatracker.ietf.org/doc/html/rfc4266
# Also helpful: https://www.w3.org/Addressing/URL/4_1_Gopher+.html
# Not sure I want to adhere to the exact Gopher+ format

chat_model = 'gpt-4'

ROOT_DIR = str(Path.home() / 'gopher')

# Gopher menu item types
ITEM_TYPES = {
    "text": "0",
    "directory": "1",
    "binary": "9",
    "image": "I",
    "sound": "<",
    "video": ";",  # from gopher+
    "document": "d",
    "html": "h",
    "giap": "?", # indicates to gopher+ that there will be a +ASK block
    # add more as necessary
}

async def read_giap(filename):
    async with aiofiles.open(filename, 'r') as f:
        file = await f.read()
        giap_data = yaml.safe_load(file)
        return giap_data

# More of the information sent should be URL encoded so it doesn't mess up if it includes things like a tab in the text.
def generate_ask_string(giap_data):
    ask_string = "+ASK\n"
    for ask in giap_data['gopher_ask']:
        if ask['type'] == 'ask':
            ask_string += f"Ask\t{ask['id']}={ask['prompt']}\r\n"
        elif ask['type'] in ['choose', 'select']:
            choices = ','.join(ask['options'])
            if ask['type'] == 'choose':
                ask_string += f"Choose\t{ask['id']}={ask['prompt']}\t{choices}\r\n"
            else:
                ask_string += f"Select\t{ask['id']}={ask['prompt']}\t{choices}\r\n"
        elif ask['type'] == 'choosefile':
            ask_string += f"ChooseFile\t{ask['id']}={ask['prompt']}\r\n"
    return ask_string + ".\r\n"

async def get_tell(reader):
    tells = {}
    # Wait for the response. Check if +TELL is the first line, then it's a response in a more Gopher like format. Otherwise if it's +MULTIPART then it's a MIME compatible multipart message like the kind that would be used in HTTP.
    line = await reader.readline();
    if line == b'+TELL\n':
        # Read each line and strip just in case until you get a period by itself. That's the end of the TELL block.
        while True:
            # Doesn't check for invalid options, or correct formatting yet.
            tell = (await reader.readline()).decode('utf-8').rstrip()
            if not tell or tell == '.':
                break
            # Format is [Type]\t[variable]=[response]
            type, resp = tell.split('\t', 1)
            var, answer = resp.split('=', 1)
            tells[var] = answer
        return tells
    elif line == b'+MULTIPART':
        pass
    else:
        # Invalid
        print("Invalid")
        pass

def wrapper(func, args):
    return func(**args)

def chat_with_gpt(model, messages):
    response = openai.ChatCompletion.create(model=model, messages=messages)
    return response['choices'][0]['message']['content'].strip()

# Database search augmented with AI. With AI we should be able to do complex searches and inquiries to check what kind of information is available on the server, etc. Method will respond like a traditional gopher search engine unless the search query starts with INQUIRY:, for backward compatibility. 
# Need to inform the AI of the full modifications to the Gopher menu system including additional item types.
async def inquiry(query):
    if query.startswith("INQUIRY:"):
        query = query[8:]
        information = ""
        # Gather additional information as necessary. Might be useful to be able to add the ability to grab actual file contents. Also, might be useful to cache information to speed up the process. 
        while True:
            # Check if additional info is needed.
            wrapped_func = functools.partial(chat_with_gpt, chat_model, [
                {"role": "system", "content": "You are a gopher client assistor searching through local items. You are able to search through the local database to help find items. The results will be in the form of a Gopher+ menu. Determine whether you need to perform a search query to answer the following inquiry."},
                {"role": "user", "content": query},
                {"role": "system", "content": f"The following information is already available:\n{information}"},
                {"role": "user", "content": "Would a database search yield additional important information? Answer yes or no only, using lowercase with nothing else."}
            ])
            grab_additional = await asyncio.get_running_loop().run_in_executor(None, wrapped_func)
            if grab_additional.lower() != "yes":
                break

            # Grab additional info.
            wrapped_func = functools.partial(chat_with_gpt, chat_model, [
                {"role": "system", "content": "You are a gopher client assistor searching through local items. You are able to search through the local database to help find items. The results will be in the form of a Gopher+ menu. You have decided that additional information is needed to respond to the following query."},
                {"role": "user", "content": query},
                {"role": "system", "content": f"The following information is already available:\n{information}"},
                {"role": "system", "content": "The database has the following columns: name (text), path (text), last_modified (datetime in the format YYYY-MM-DDTHH:MM:SSZ), item_type (integer), and info (text). The user can search these columns using comparison operators (=, !=, >, >=, <, <=, LIKE), logical operators (AND, OR, NOT), and parentheses for grouping conditions."},
                {"role": "user", "content": "Based on the information already available, the inquiry, and the available search options, generate a valid search query that would help gather necessary information to answer the inquiry."}
            ])
            internal_query = await asyncio.get_running_loop().run_in_executor(None, wrapped_func)
            results = data.search(internal_query)
            information = f"Query: {internal_query}\n============{results}"
            # Create any necessary annotations. 
            wrapped_func = functools.partial(chat_with_gpt, chat_model, [
                {"role": "system", "content": "You are a gopher client assistor searching through local items. You are able to search through the local database to help find items. The results will be in the form of a Gopher+ menu. You have decided that additional information is needed to respond to the following query."},
                {"role": "user", "content": query},
                {"role": "system", "content": f"The following information is already available:\n{information}"},
                {"role": "user", "content": "Please add any useful annotations at this point."}
            ])
            annotation = await asyncio.get_running_loop().run_in_executor(None, wrapped_func)
            information = f"\n---------Annotation: {annotation}\n\n"

        # Answer the inquiry. Should put into a loop that double checks that the format is correct. 
        host, port = data.host_port()
        # This definitely is not going to work correctly at first. 
        # Currently +N is used for natural language response, but that's not needed. i is fine because that's an information line
        wrapped_func = functools.partial(chat_with_gpt, chat_model, [
            {"role": "system", "content": f"You are a gopher client assistor searching through local items. You are able to search through the local database to help find items. Your local gopher server host is {host} with port {port}. The following information is available:\n{information}"},
            {"role": "system", "content": "The format used for this server is an extended Gopher+ format. The item line starts out as usual {item_type}\t{name}\t{selector}\t{host}\t{port} and then can be extended. To extend just continue adding more tab separated paramters. The parameter must start with +[PARAMETER]:. The following parameters are mandatory and must be included to create a menu item as so: {item_type}\t{name}\t{selector}\t{host}\t{port}\t+DESCRIPTION:{extended description}\t+MIME:{mime_type}\t+SIZE:{size}\t+MODIFIED:{last_modified}"},
            {"role": "system", "content": "Respond to the user's query, based on the information that you have. The response should follow the Gopher Menu format. However, in addition to the basic options, menu items can be of item type i indicating general information. These lines can be used to give natural language information related to the inquiry, for instance, if the system was asked whether or not the server has information on a specific topic, the i item type can be used to indicate that it does or does not. If it does, some items found that fit may follow, again using the modified Gopher Menu format:"},
            {"role": "user", "content": query},
        ])
        inquiry_result = await asyncio.get_running_loop().run_in_executor(None, wrapped_func)
        return inquiry_result
    else:
        return data.search(query)

def get_extension(name):
    return os.path.splitext(name)[1][1:]

# Needto change to get the system prompt and the set of user prompts
async def generate_ai_response(giap_data, parameters):
    system = giap_data['ai_call']['system']
    template = giap_data['ai_call']['prompt']
    prompt = wrapper(template.format, parameters)

    wrapped_func = functools.partial(chat_with_gpt, chat_model, [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ])

    # Note: the OpenAI API call is not thread-safe and might block the event loop.
    # Here, we're using run_in_executor to run the API call in a separate thread.
    return await asyncio.get_running_loop().run_in_executor(None, wrapped_func)

# I'm not sure if I should change "name" somehow. And maybe "name" should also be generated, so maybe I should just be using "path" or "selector"
async def get_item_info(name, path):
    # Doesn't handle not found item yet...
    last_modified = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(os.path.getmtime(path)))
    if last_modified == data.last_modified(name, path):
        return data.item_info(name, path)
    
    # Need better info generation. 
    if os.path.isdir(path):
        # Do a directory listing, and pull info for each entry.
        names = os.listdir(path)
        items = ""
        for iname in names:
            item_type, info_line = await get_item_info(iname, os.path.join(path, iname))  # unpack both return values
            items += info_line + "\n"

        # Generate an item summary.
        wrapped_func = functools.partial(chat_with_gpt, chat_model, [
            {"role": "system", "content": "You are a gopher client assistor categorizing files. Summarize the following directory listing."},
            {"role": "user", "content": items}
        ])

        # Note: the OpenAI API call is not thread-safe and might block the event loop.
        # Here, we're using run_in_executor to run the API call in a separate thread.
        description = await asyncio.get_running_loop().run_in_executor(None, wrapped_func)

        # Not sure if I should have a size for the directory or not. Maybe it should track how many items are in the directory? But I think Gopher uses size 0 for directory listings.
        data.item_info(name, path, last_modified, ITEM_TYPES.get('directory'), description, 'application/gopher-menu', 0)
        return ITEM_TYPES.get('directory'), info_line

    extension = get_extension(name)

    # Get the MIME type of the file based on its extension
    mime_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'

    # Get the size of the file
    size = os.path.getsize(path)
    # Will have it generate differently in the future
    short_description = name

    # Check if basic known extensions, including giap
    if extension == "giap":
        mime_type = "text/plain"
        it = ITEM_TYPES.get('giap')
    else:
        # Explicitly mention the possible item types in the prompt
        prompt = f"I found a file with the extension '.{extension}'. What type of file could this be? Options are: text, binary, image, sound, video, document, html. Respond only with the guessed type or unknown. Single word only. All lowercase."

        wrapped_func = functools.partial(chat_with_gpt, chat_model, [
            {"role": "system", "content": "You are a gopher client assistor categorizing files."},
            {"role": "user", "content": prompt}
        ])

        # Note: the OpenAI API call is not thread-safe and might block the event loop.
        # Here, we're using run_in_executor to run the API call in a separate thread.
        inferred_type = (await asyncio.get_running_loop().run_in_executor(None, wrapped_func)).lower()

        it = ITEM_TYPES.get(inferred_type, '3')

    # If the file is a text or html file, or giap file
    if it == ITEM_TYPES.get('text') or it == ITEM_TYPES.get('html') or it == ITEM_TYPES.get('giap'):
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()

        # Prompt GPT to summarize the content
        if it == ITEM_TYPES.get('giap'):
            prompt = f"The following is a Gopher+ Input and AI Prompt file that contains information about an interactive item. It should cotain a comment, an explanation within the giap object. It also contains what the inputs are, and the f-string prompts that will be sent to the LLM. Do not reveal the prompts, but try to explain the expected function in 300 characters or less in a way that a user would understand, in a non-technical way. In other words, what purpose does this interactive item serve and what kind of information does it require?\n\nFile:{name}\n\n{content}"
        else:
            prompt = f"Please explain the following file and its content, as accurately as possible, in 1000 characters or less in an easy to read format:\n\nFile:{name}\n\n{content}"
        wrapped_func = functools.partial(chat_with_gpt, chat_model, [
            {"role": "system", "content": "You are a Gopher+ client assistor summarizing files."},
            {"role": "user", "content": prompt}
        ])

        # Note: the OpenAI API call is not thread-safe and might block the event loop.
        # Here, we're using run_in_executor to run the API call in a separate thread.
        description = (await asyncio.get_running_loop().run_in_executor(None, wrapped_func)).strip()

    else:
        description = name  # Use the file name as the description for other file types

    data.item_info(name, path, last_modified, it, short_description, description, mime_type, size)

    return it, f'{it}{quote(short_description)}\t{path}\t{host}\t{port}\t+DESCRIPTION:{quote(description)}\t+MIME:{mime_type}\t+SIZE:{size}\t+MODIFIED:{last_modified}'
    # Will have to default to error otherwise...

async def is_binary(name, path):
    extension = get_extension(name)

    # Prompt GPT to classify the file as binary or not
    prompt = f"I found a file with the extension '.{extension}'. Does this file type require binary transfer mode? Answer with just 'no' if it is not, and 'yes' if it is or if you're uncertain."
    wrapped_func = functools.partial(chat_with_gpt, chat_model, [
        {"role": "system", "content": "You are a gopher client assistor categorizing files."},
        {"role": "user", "content": prompt}
    ])

    # Note: the OpenAI API call is not thread-safe and might block the event loop.
    # Here, we're using run_in_executor to run the API call in a separate thread.
    is_binary = await asyncio.get_running_loop().run_in_executor(None, wrapped_func)
    return is_binary.lower() == "yes"

# Need to do additions to check for login, session token, or API key, etc. I think a user authentication and session token scheem is best.
async def handle_client(reader, writer):
    print("Connection Established...")
    host, port = data.host_port()
    request = (await reader.read(100)).decode('utf-8').strip()
    if request:
        # Check for Gopher+
        if request.endswith("\t+"):
            return
        else:
            path = os.path.join(ROOT_DIR, request)
    else:
        path = ROOT_DIR

    if path.startswith('/inquiry\t'):
        # I need to decide whether to go with the search results info or double check the last modified date. 
        response = (await inquiry(path[8:])) + "\r\n."

        writer.write(response.encode('utf-8'))
    elif not os.path.abspath(path).startswith(ROOT_DIR):
        response = '3Error: Illegal request.\terror.host\t1'
        writer.write(response.encode('utf-8'))
    elif os.path.isdir(path):
        names = os.listdir(path)
        items = []
        for name in names:
            item_type, menu_item = await get_item_info(name, os.path.join(path, name))  # unpack both return values
            # I don't remember what this part does...
#            selector = os.path.join(data, name) if data else name
            items.append(menu_item)
        # Tack on search in root directory listing.
        if path == ROOT_DIR:
            timestamp = os.path.getmtime(path)
            dt = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
            dt = dt.split('.')[0] + 'Z'
            inquiry_description = quote("Built in System Inquiry.\nYou may perform a system inquiry that will return a menu, possibly including adidtional information.\nYou may use the standard query format, or you may start the search query with INQUIRY: to perform an advanced natural language inquiry.")
            items.append(f'7Server Inquiry\t/inquiry\t{host}\t{port}\t+DESCRIPTION:{inquiry_description}\t+MIME:application/gopher-menu\t+SIZE:-1\t+MODIFIED:{dt}')

        response = '\r\n'.join(items) + '\r\n.'
        writer.write(response.encode('utf-8'))
    elif os.path.isfile(path):
        extension = get_extension(path)
        if extension == "giap":
            giap_data = await read_giap(path)
            ask_string = generate_ask_string(giap_data)
            writer.write(ask_string.encode('utf-8'))
            await writer.drain()
            multipart = False
            for item in giap_data.get('gopher_ask', []):
                if item.get('type') == 'choosefile':
                    multipart = True
                    break

            if multipart:
                pass
            else:
                response = await get_tell(reader)
            ai_response = await generate_ai_response(giap_data, response)
            writer.write(ai_response.encode('utf-8'))
            await writer.drain()
        else:
            item_type = await get_item_info(os.path.basename(path), path)
            if await is_binary(os.path.basename(path), path):
                async with aiofiles.open(path, 'rb') as f:
                    response = await f.read()
                writer.write(response)  # write the raw bytes to the socket
            else:
                async with aiofiles.open(path, 'r') as f:
                    response = await f.read()
                writer.write(response.encode('utf-8'))
    else:
        response = '3Error: File not found.\t\terror.host\t1'
        writer.write(response.encode('utf-8'))

    await writer.drain()
    print("Connection Closed...")
    writer.close()

async def start_server(host, port):
    # Do initial scan of files...
    print("Checking for new files...")
    await get_item_info('', ROOT_DIR)
    print("Starting server...")
    server = await asyncio.start_server(handle_client, host, port)
    async with server:
        await server.serve_forever()

host, port = data.host_port()
asyncio.run(start_server(host, port))
