# OctoRAG
Lightweight agents that use GitHub Search API to do RAG for tasks such as recommending projects and libraries, and generating code with their selections that they then publishes to GitHub as a private repository. Written in Python using LangGraph.

## Dependencies
- `httpx==0.28.1`
- `langchain==0.3.26`
- `langchain_core==0.3.67`
- `langchain_mcp_adapters==0.1.8`
- `langgraph==0.5.0`
- `mcp==1.10.1`
- `python-dotenv==1.1.1`
- `setuptools==80.9.0`
- `typing_extensions==4.14.0`

You can install these using the `requirements.txt` file in the root directory. This would be `pip install -r requirements.txt` if using pip from the root directory.

## Features
At present, large language models are limited to the knowledge they have been trained on when they write responses. This library provides agentic extensions that allow a model to:
- Browse GitHub for repositories based on natural language keywords
- Retrieve the full file tree of a GitHub repository
- Read arbitrary files inside of a repository
- Create (private) repositories
- Upload files to repositories

In addition, it provides a prompt-to-code workflow that can go straight to a prompt to a full repository with code written to implement said prompt uploaded privately to GitHub. This exists as a single-agent local application, or as a multi-agent MCP client that connects to an MCP server hosting the tools. 

## Usage
OctoRAG can be run locally (as a single agent), or as a client that connects to an MCP server (as a multi-agent workflow). **It is strongly advised to do the latter, as the MCP client implements a multi-agent workflow instead of a single agent. This makes the model's running more robust and improves the code quality.**

### Running OctoRAG locally
You need a `.env` file that contains the following:
- `ANTHROPIC_API_KEY`: Your Anthropic key that is used to query large language models.
- `GH_ACCESS_TOKEN`: A GitHub access token. This token should have permissions to search GitHub for repositories, via API calls. If you wish for the model to be able to upload the generated code to GitHub, this token must also have permissions to create and manage repositories you own. OctoRAG will NOT access any repositories other than the one it creates to contain your code. You can check the code at `octorag_mcp_client.py` yourself to see the system prompts!

From there, simply do the following to query the model!
```python
from octorag import OctoRAG

model = OctoRAG(
    path_to_env_file = "path/to/env/file" # location of your .env file. Looks in root directory by default
)

q = model.query(
    "I need an open-source raytracer for a bigger project I'm working on. It needs to be able to be called as a library, like I can just call a `raytrace()` function and it draws the input scene for me. I'm working in Rust. Give me a single up-to-date recommendations."
)
```

## Running OctoRAG as an MCP client
You must first provision an MCP server that implements the tools in `octorag_mcp_server.py`. This server will need a GitHub access token stored as an environment variable `GH_ACCESS_TOKEN`. 

The simplest way to do this is to simply copy and run `octorag_mcp_server.py` on your server. It will need a `.env` file containing the following:
- `GH_ACCESS_TOKEN`: A GitHub access token. This token should have permissions to search GitHub for repositories, via API calls. If you wish for the model to be able to upload the generated code to GitHub, this token must also have permissions to create and manage repositories you own. OctoRAG will NOT access any repositories other than the one it creates to contain your code. You can check the code at `octorag_mcp_client.py` yourself to see the system prompts!

To use this MCP server, you need a `.env` file containing the following in the pace where you wish to store the client:
- `ANTHROPIC_API_KEY`: Your Anthropic key that is used to query large language models.

From there, you can simply do the following:
```python
from octorag_mcp_client import OctoRAG_MCP

model = OctoRAG_MCP(
    path_to_env_file = "path/to/env/file", # location of your .env file. Looks in root directory by default
    mcp_url = "http://your-mcp-server.com/mcp/endpoint", # location of your MCP server. Defaults to http://localhost:8000/mcp, the endpoint location of octorag_mcp_server.py
    debug = False # Set if you want the messages that call tools. Default False. It can be reset on the fly at model.debug.
)


q = model.query(
            "Write code in Python to create a HTTP server that can handle GET and POST requests"
            " It should be able to retrieve stats of NBA players from the NBA API when asked."
            " And it should predict the probability of a team winning a game against another team, based on the stats of the players."
        )
```

`OctoRAG_MCP.query` returns an async generator that contains all the messages returned by the multi-agent workflow.

You can see the results of running this code block [here](https://github.com/Akhil841/nba-stats-prediction-api-3422643/)!
