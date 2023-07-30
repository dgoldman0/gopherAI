# GIAP (Gopher+ Input and AI Prompt Document Format (".giap"))

One of the additions for Gopher+NLP that should be core to the system is the inclusion of interactive services that can be accessed by large language models. GIAP files define various parameters that allow for easy deployment of such services by defining the model, creating predefined prompt sets, etc. The current design is just a draft and is subject to change.

## 1. Introduction

The Gopher+ Input and AI Prompt (".giap") document format is designed to specify a set of Gopher+ ASK options and an AI prompt, with the responses embedded. It uses a human-readable and easy-to-use syntax based on YAML and Python's f-string syntax.

## 2. File Extension

Files conforming to this format should use the extension ".giap".

## 3. File Structure

The file consists of two main sections, each represented as a key in the top-level YAML dictionary: `gopher_ask` and `ai_call`.

### 3.1. giap
- `explanation`: the explanation is a human readable, and thus AI readable explanation of the interactive file's functionality. 
 
### 3.2. gopher_ask

This section defines the Gopher+ ASK inputs. It contains a list of dictionaries. Each dictionary must contain the following keys:

- `id`: A unique identifier for the input.
- `type`: The type of the input. It can be one of the following: 'ask', 'choose', 'select', or 'choosefile'.
- `prompt`: The prompt for 'ask' and 'choosefile' types.
- `options`: The list of options for 'choose' and 'select' types.

	### 3.3. ai_call

This section defines the AI prompt. It contains a dictionary with the following key:

- `tokens`: The maximum number of tokens to be generated. 
- `system`: The AI system string which is used to adjust the behavior of the LLM. 
- `prompt`: One or more AI prompt strings. These string use Python's f-string syntax to include variables from the `gopher_ask` section. The variable names correspond to the `id` of the Gopher+ ASK inputs.
- 
## 4. Example

Here is an example of a ".giap" file:

```yaml
giap:
  - explanation: "I'll write a detailed adventure story of a character exploring a planet, where the character has certain personal preferences and the planet has certain features."
gopher_ask:
  - id: 'character_name'
    type: 'ask'
    prompt: "What is the character's name?"
  - id: 'preferred_transport'
    type: 'choose'
    prompt: "What is your character's preferred mode of space travel?"
    options:
      - 'Space Shuttle'
      - 'Teleportation'
      - 'Star Cruiser'
  - id: 'favorite_space_food'
    type: 'choose'
    prompt: "What is your character's favorite space food?"
    options:
      - 'Nutrient-rich Gel Capsules'
      - 'Synthetic Protein Bars'
      - 'Alien Fruit'
  - id: 'background_music'
    type: 'select'
    prompt: 'What kind of background music does your character enjoy while exploring?'
    options:
      - 'Epic orchestral music'
      - 'Ambient electronic music'
      - 'Space rock'
  - id: 'planet_name'
    type: 'ask'
    prompt: 'What is the name of the planet to be explored?'
  - id: 'planet_feature'
    type: 'choose'
    prompt: "What is a distinctive feature of the planet?"
    options:
      - 'A landscape full of crystalline formations'
      - 'Rich with alien flora and fauna'
      - 'A mysterious ancient alien civilization'
ai_call:
  tokens: 1000
  system: 'You are an imaginative science fiction writer.'
  prompt: 'Write an adventure story about {character_name}, who travels by {preferred_transport}, enjoys {favorite_space_food} during the journey, and listens to {background_music}. The story takes place on the planet {planet_name}, which is known for its {planet_feature}.'
```

## 5. Usage

The ".giap" file should be read and parsed by a program that can interpret YAML and substitute variables using Python's f-string syntax. The `gopher_ask` section should be used to generate Gopher+ ASK prompts, and the user's responses should be collected. The `ai_call` section should be used to generate the AI prompt, substituting the user's responses into the prompt string.