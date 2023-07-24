import tkinter as tk
from tkinter import ttk, simpledialog
import asyncio
import aiofiles
import os
import subprocess

import tkinter.filedialog

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes

def generate_tell(ask_responses):
    tell_string = "+TELL\n"
    for var, data in ask_responses.items():
        ask_type = data['type']
        value = data['value']
        if ask_type == 'Ask':
            tell_string += f"Tell\t{var}={value}\r\n"
        elif ask_type in ['Choose', 'Select']:
            choices = value
            # If the value is a list, convert to comma separated
            if isinstance(choices, list):
                choices = ','.join(choices)
            tell_string += f"Choices\t{var}={choices}\r\n"
    return tell_string + ".\r\n"

def create_multipart_message(ask_responses):
    msg = MIMEMultipart()
    for var, data in ask_responses.items():
        ask_type = data['type']
        value = data['value']
        if ask_type in ["Ask", "Choose"]:
            msg.attach(MIMEText(f'Content-Disposition: form-data; name="{var}"\r\n\r\n{value}'))
        elif ask_type == "ChooseFile":
            if os.path.isfile(value):
                mime_type, _ = mimetypes.guess_type(value)
                if mime_type is None:
                    mime_type = "application/octet-stream"
                main_type, sub_type = mime_type.split("/", 1)
                with open(value, "rb") as file:
                    if main_type == "text":
                        file_data = MIMEText(file.read().decode(), _subtype=sub_type)
                    else:
                        file_data = MIMEBase(main_type, sub_type)
                        file_data.set_payload(file.read())
                        encoders.encode_base64(file_data)
                file_data.add_header("Content-Disposition", "form-data", name=var, filename=os.path.basename(value))
                msg.attach(file_data)
            else:
                msg.attach(MIMEText(f'Content-Disposition: form-data; name="{var}"\r\n\r\n{value}'))
        elif ask_type == "Select":
            for choice in value:
                msg.attach(MIMEText(f'Content-Disposition: form-data; name="{var}"\r\n\r\n{choice}'))
    return msg.as_string()

# Need to adjust to have the variable type and then actually grab the file and its MIME type.
class AskDialog(tk.simpledialog.Dialog):
    def __init__(self, parent, title=None, ask_inputs=None):
        self.ask_inputs = ask_inputs
        self.results = []
        tk.simpledialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        self.widgets = []
        for i, (ask_type, ask_prompt, ask_var, ask_choices) in enumerate(self.ask_inputs):
            tk.Label(master, text=ask_prompt).grid(row=i)
            if ask_type == "Ask":
                entry = tk.Entry(master)
                entry.grid(row=i, column=1)
                self.widgets.append(entry)
            elif ask_type == "Choose":
                if ask_choices:
                    ask_choices_list = ask_choices
                    var = tk.StringVar(value=ask_choices_list[0])
                    dropdown = tk.OptionMenu(master, var, *ask_choices_list)
                    dropdown.grid(row=i, column=1)
                    self.widgets.append((dropdown, var))
            elif ask_type == "Select":
                if ask_choices:
                    ask_choices_list = ask_choices
                    listbox = tk.Listbox(master, selectmode=tk.MULTIPLE)
                    listbox.grid(row=i, column=1)
                    for choice in ask_choices_list:
                        listbox.insert(tk.END, choice)
                    self.widgets.append(listbox)
            elif ask_type == "ChooseFile":
                var = tk.StringVar()
                button = tk.Button(master, text="Select File", command=lambda: var.set(tk.filedialog.askopenfilename()))
                button.grid(row=i, column=1)
                self.widgets.append((button, var))
        return self.widgets[0]

    def apply(self):
        results = {}
        for i, widget in enumerate(self.widgets):
            ask_type, _, ask_var, _ = self.ask_inputs[i]  # get ask_type and ask_var
            result = {}
            if isinstance(widget, tk.Entry):
                result["type"] = "Ask"
                result["value"] = widget.get()
            elif isinstance(widget, tuple) and isinstance(widget[0], tk.Button):
                result["type"] = "ChooseFile"
                result["value"] = widget[1].get()
            elif isinstance(widget, tk.Listbox):
                result["type"] = "Select"
                result["value"] = [widget.get(i) for i in widget.curselection()]
            else:  # OptionMenu for "Choose"
                result["type"] = "Choose"
                result["value"] = widget[1].get()
            results[ask_var] = result
        self.results = results

class GopherClient:

    ITEM_TYPES = {
        "0": "(TEXT)",
        "1": "(DIR)",
        "9": "(BIN)",
        "I": "(IMAGE)",
        "<": "(SOUND)",
        ";": "(VIDEO)",
        "d": "(DOC)",
        "h": "(HTML)",
        "7": "(SEARCH)",
        "?": "(INTERACTIVE)", # indicates to gopher+ that there will be a +ASK block
    }

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.menu = []
        self.location = ''
        self.menu_history = []  # stack to store menu history
        self.last_query = ['', None]  # to store last query for re-fetching pending interaction

    async def fetch(self, selector, query = None, download = False, wait = False):
        self.last_query = [selector, query]
        reader, writer = await asyncio.open_connection(self.host, self.port)
        if query is not None:
            message = self.location + selector + '\t' + query + "\r\n"
        else:
            message = self.location + selector + "\r\n"
        writer.write(message.encode('utf-8'))
        await writer.drain()

        if wait:
            # The first line should be a +ASK
            line = await reader.readline();
            print(line)
            if line != b'+ASK\n':
                print("INVALID")
                return
            ask_inputs = []
            while True:
                # Doesn't check for invalid options, or correct formatting yet.
                ask = (await reader.readline()).decode('utf-8').rstrip()
                if not ask or ask == '.':
                    break

                ask_type, rest = ask.split("\t", 1)
                ask_var, ask_prompt = rest.split("=", 1)
                ask_choices = None

                if "\t" in ask_prompt:
                    ask_prompt, ask_choices = ask_prompt.split("\t", 1)

                if ask_choices is not None:
                    ask_choices = ask_choices.split(',')
                input = (ask_type, ask_prompt, ask_var, ask_choices)
                ask_inputs.append(input)

            dialog = AskDialog(self.root, "Input", ask_inputs)
            ask_responses = dialog.results
            # If the +ASK block contains a file, which therefore could be a large binary file, we'll use multipart. Otherwise we'll use tab separated as is closer to the original Gopher protocol.
            multipart = False
            for input in ask_inputs:
                if input[0] == 'ChooseFile':
                    multipart = True

            message = ""
            if multipart:
                message = create_multipart_message(ask_responses)
            else:
                message = generate_tell(ask_responses)

            print(message)
            writer.write(message.encode('utf-8'))
            await writer.drain()

        temp_menu = []  # temporary menu to store fetched items

        if download:
            print(type)
            filename = selector.split('/')[-1:][0]

            async with aiofiles.open(filename, 'wb') as fd:
                while True:
                    line = await reader.readline()
                    if not line or line == b'.':
                        break
                    await fd.write(line)

            if (os.name == 'nt'):  # For Windows
                os.startfile(filename)
            elif (os.name == 'posix'):  # For Unix or Linux
                subprocess.call(('xdg-open', filename))
        else:
            if not query and selector != '':
                self.location += selector + '/'

            item_info = None
            while True:
                line = await reader.readline()
                if not line or line == b'.':
                    break
                line = line.decode('utf-8').rstrip()
                if line.startswith('+INFO: '):
                    item_info = line[7:].split('\t')
                else:
                    parts = line.split('\t')
                    item = [parts[0][0], parts[0][1:]] + parts[1:]
                    if item_info is not None:
                        item.extend(item_info)
                    item_info = None
                    temp_menu.append(item)

        writer.close()
        if temp_menu:  # if the fetched menu is not empty
            self.menu = temp_menu  # set current menu to the fetched menu
            self.menu_history.append((self.location, self.menu))  # add fetched menu to the history
            if len(self.menu_history) > 1:
                self.back_button.config(state=tk.NORMAL)  # enable back button
        await writer.wait_closed()

    def start(self):
        root = tk.Tk()
        root.title("Gopher+ Client")
        style = ttk.Style()
        style.configure("Treeview", rowheight=30) # increase row height
        tree = ttk.Treeview(root)

        self.root = root
        self.tree = tree

        # Create a scrollbar and attach it to tree
        scrollbar = tk.Scrollbar(root)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)

        tree["columns"]=("Filetype", "Filename", "Size", "Timestamp", "Description")
        tree.column("#0", width=0, stretch=tk.NO)
        tree.heading("#0", text='', anchor=tk.W)

        for col in tree["columns"]:
            tree.column(col, anchor=tk.W)
            tree.heading(col, text=col, anchor=tk.W)

        # Add items to treeview
        self.populate_tree()

        tree.pack(side=tk.TOP,fill=tk.X)

        back_button = tk.Button(root, text="Back", command=self.go_back)
        back_button.pack()
        self.back_button = back_button  # keep a reference to the back_button
        if len(self.menu_history) <= 1:
            self.back_button.config(state=tk.DISABLED)  # Initially disable the back button

        def on_select(event):
            item = tree.selection()[0]
            values = tree.item(item)['values']

            dt = values[0]
            filename = values[1]

            if dt == '(DIR)':
                asyncio.run(self.fetch(filename))
            elif dt == '(SEARCH)':
                query = simpledialog.askstring("Search", "Enter your search:")
                if query is not None:
                    asyncio.run(self.fetch(filename, query))
            elif dt == "(INTERACTIVE)":
                # Get the ASK inputs then render a dialogue, get input, and respond, then it'll generate the response.
                asyncio.run(self.fetch(filename, download = True, wait = True))
            else:
                asyncio.run(self.fetch(filename, download = True))

            root.after(100, self.populate_tree)

        tree.bind('<Double-1>', on_select)  # Bind double click to on_select
        root.mainloop()

    def populate_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for item in self.menu:
            filetype = self.ITEM_TYPES.get(item[0], "(UNKNOWN)")
            filename = item[1]
            description = item[2]
            size = item[9] if item[9] != "-1" else ""
            timestamp = item[10] if item[10] else ""
            self.tree.insert('', 'end', values=(filetype, filename, size, timestamp, description))

    def go_back(self):
        if len(self.menu_history) > 1:  # ensure that we have a history to go back to
            self.menu_history.pop()  # remove current menu from history
            self.location = self.menu_history[-1][0]
            self.menu = self.menu_history[-1][1]  # set menu to last menu in history
            self.populate_tree()  # populate treeview
            if len(self.menu_history) <= 1:
                self.back_button.config(state=tk.DISABLED)  # disable the back button if we are at the start

gc = GopherClient('localhost', 10070)
asyncio.run(gc.fetch(''))
gc.start()
