import yaml

def read_giap(filename):
    with open(filename, 'r') as file:
        giap_data = yaml.safe_load(file)
    return giap_data

def generate_ask_string(giap_data):
    ask_string = "+ASK\n"
    for ask in giap_data['gopher_ask']:
        if ask['type'] == 'ask':
            ask_string += f"Ask: {ask['prompt']}=:{ask['id']}\n"
        elif ask['type'] in ['choose', 'select']:
            choices = ':'.join(ask['options'])
            if ask['type'] == 'choose':
                ask_string += f"Choose: {ask['id']}={choices}\n"
            else:
                ask_string += f"Select: {ask['id']}={choices}\n"
        elif ask['type'] == 'choosefile':
            ask_string += f"ChooseFile: {ask['prompt']}=:{ask['id']}\n"
    return ask_string

def generate_ai_prompt(giap_data):
    return giap_data['ai_call']['prompt']

def main():
    giap_data = read_giap('example.giap')
    ask_string = generate_ask_string(giap_data)
    ai_prompt = generate_ai_prompt(giap_data)
    print('Gopher ASK Request:', ask_string)
    print('AI Prompt:', ai_prompt)

if __name__ == "__main__":
    main()
