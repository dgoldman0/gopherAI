const API_KEY = process.env.OPENAI_API_KEY;  // Replace with your actual OpenAI API key
const axios = require('axios');

const OPENAI_CHAT_API_URL = 'https://api.openai.com/v1/chat/completions';  // Notice the change in the endpoint URL
/**
 * Fetches a completion from OpenAI based on a series of messages.
 * 
 * @param {Array} messages - An array of message objects, e.g. [{role: 'user', content: 'Hello'}].
 * @param {Object} [options={}] - Optional settings for the completion.
 * @param {string} [options.model='gpt-4'] - The model to use for completion.
 * @param {number} [options.maxTokens=150] - The maximum length of the response.
 * @param {number} [options.temperature=0.7] - Sampling temperature for randomness in response.
 * @returns {Promise<string>} - The assistant's response.
 */

async function complete(messages, options = {}) {
    const {
        model = 'gpt-4',
        maxTokens = 150,
        temperature = 0.7
    } = options;

    try {
        const response = await axios.post(OPENAI_CHAT_API_URL, {
            model,
            messages,
            max_tokens: maxTokens,
            temperature
        }, {
            headers: {
                'Authorization': `Bearer ${API_KEY}`,
                'Content-Type': 'application/json'
            }
        });

        return response.data.choices[0].message.content.trim();
    } catch (error) {
        console.error('Error calling OpenAI API:', error.message);
        if (error.response && error.response.data) {
            console.error('Detailed error:', JSON.stringify(error.response.data, null, 2));
        }
        throw error;  // Re-throw the error if you want it to be handled further up the call stack
    }
}

class Assistant {
    constructor(apiKey) { this.apiKey = apiKey; this.chatHistory = []; }
    setClient(client) { this.client = client; }
    setView(view) { this.view = view; }

    async processInput(prompt) {
        if (prompt) {
            this.chatHistory.push({role: 'user', content: prompt});

            // Things to add
            //
            // Add this back when we get location included again
            // Current Directory: ${this.client.location}
            // 
            // More commands, maybe broken down into sections. File access needs to be added (both open and save)
 
            const systemMessageContent = `
            You are a helpful assistant. This is the data collection phase. Before you can respond to the user, you must double check to make sure you don't need to perform any internal commands. You can perform a number of operations, or just answer questions in general. The following is some general information.

            Server: ${this.client.host}:${this.client.port}
            Date and Time (UTC): ${new Date().toISOString()}
            
            Do you need to perform any additional functions before answering responding to the user? Here are the following options:
            - scan [selector]: fetches the selector as a Gopher menu
            - fetch [selector] []: fetches an item from the current gopher server.
            - grab [selector]: fetches an item from the current gopher server and downloads it
            - bfetch [selector] []: fetches a binary item from the current gopher server
            - bgrab [selector]: fetches an item from the current gopher server and downloads it
            - hop [host] [port] - hop to a different Gopher server
            - none (by itself): specifies that there's no need for additional information and to continue to the response stage.
            Please select a command to execute or none. Your response must start with a valid command. You will have a chance to write a full response after your data collection has been completed by selecting **none**.
            `;

            let messages = [
                {role: 'system', content: systemMessageContent.trim()}
            ];

            messages = messages.concat(this.chatHistory.map(({role, content}) => ({
                role,
                content
            })));

            while (true) {
                const response = await complete(messages, {apiKey: this.apiKey});
                const [command, ...parts] = response.split(' ');
                const parameters = parts.join(' ');

                if (command === 'none') {
                    break;
                } else if (command === 'scan') {
                    // Grab menu
                    menu = this.client.scan(selector);
                    info = menu.items.join(' | ');
                    // 
                } else if (command === 'fetch') {

                }
            }
        }
    }
}

module.exports = {
    Assistant    
};

