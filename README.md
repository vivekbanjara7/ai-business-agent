\# AI Business Agent 🤖



Hi! This is my AI Business Agent, a project I built using Python and Streamlit to explore how AI agents can do more than just answer questions.



The idea behind this project is simple: create an AI assistant that can understand requests, use different tools, remember useful information, and help with everyday business-related tasks.



Instead of keeping everything limited to a chatbot, I wanted to experiment with features that make an AI agent more useful in practice.



\## What can it do?



Here are some of the things the agent can currently do:



\- \*\*Have conversations:\*\* Ask questions and interact with the agent through a chat interface.

\- \*\*Search the web:\*\* Research topics using the TinyFish Search API.

\- \*\*Perform calculations:\*\* Use a calculator tool for arithmetic operations.

\- \*\*Remember information:\*\* Save useful details and retrieve them in future interactions.

\- \*\*Plan tasks:\*\* Break complex requests into smaller, manageable steps.

\- \*\*Use multiple tools:\*\* Work with more than one tool when a task requires it.

\- \*\*Stream responses:\*\* Display answers progressively instead of waiting for the entire response.

\- \*\*Switch themes:\*\* Choose Light, Dark, or System mode.

\- \*\*Manage conversations:\*\* Use a simple chat interface with starter prompts and conversation controls.



\## Technologies I used



I used the following technologies while building this project:



\- \*\*Python\*\* – Main programming language.

\- \*\*Streamlit\*\* – To build the web interface.

\- \*\*OpenRouter\*\* – To connect the application to an AI model.

\- \*\*OpenAI Python SDK\*\* – To communicate with the model through the API.

\- \*\*TinyFish Search API\*\* – To add web research capabilities.

\- \*\*Pytest\*\* – For automated testing.

\- \*\*Playwright\*\* – For browser-based UI testing.



\## Getting started



Want to run the project on your own computer? Follow these steps.



\### 1. Clone the repository



```bash

git clone YOUR\_GITHUB\_REPOSITORY\_URL

cd ai-business-agent

```



\### 2. Create a virtual environment



```bash

python -m venv .venv

```



Activate it on Windows:



```cmd

.venv\\Scripts\\activate

```



\### 3. Install the required packages



```bash

pip install streamlit openai requests pytest playwright

```



For browser-based testing, install the Playwright Chromium browser:



```bash

python -m playwright install chromium

```



\### 4. Set up your API keys



This project uses two API keys:



\- `OPENROUTER\_API\_KEY`

\- `TINYFISH\_API\_KEY`



Add your own keys to your environment variables. For Windows CMD, you can use:



```cmd

set OPENROUTER\_API\_KEY=your\_openrouter\_key

set TINYFISH\_API\_KEY=your\_tinyfish\_key

```



\*\*Important:\*\* Keep your API keys private. Never upload them to GitHub or share your `.env` file.



\### 5. Start the application



Once everything is installed and configured, run:



```bash

python -m streamlit run app.py

```



Streamlit will start the application and provide a local URL that you can open in your browser.



\## Testing the project



I also added automated tests to check whether the different parts of the agent are working correctly.



The current test suite includes \*\*44 passing unit and integration tests\*\* covering:



\- Calculator operations

\- Web search functionality

\- Persistent memory

\- Tool execution

\- Agent workflow and planning



To run these tests:



```bash

pytest -p no:cacheprovider tests/test\_calculator.py tests/test\_web\_search.py tests/test\_memory.py tests/test\_tool\_executor.py tests/test\_agent.py -v

```



I also use Playwright to test important interactions in the actual application interface:



```bash

python tests/test\_ui.py

```



\## Project structure



Here is a simplified overview of the main project files:



```text

ai-business-agent/

│

├── app.py                  # Streamlit user interface

├── main.py                 # Main agent logic

├── tools.py                # Available tools and execution

├── memory.py               # Persistent memory handling

│

├── tests/

│   ├── conftest.py

│   ├── test\_calculator.py

│   ├── test\_web\_search.py

│   ├── test\_memory.py

│   ├── test\_tool\_executor.py

│   ├── test\_agent.py

│   └── test\_ui.py

│

├── .streamlit/

│   └── config.toml

│

└── .gitignore

```



\## A little about the project



This project has been a practical learning experience for me.



While building it, I explored how AI models interact with external tools, how an agent can maintain memory, how multiple tools can work together, and how to test an application beyond simply checking whether it runs.



There is still room for improvement, and that's part of the journey. My goal is to keep learning, improving the code, and building more capable AI-powered applications.



Thanks for checking out my project! ⭐

