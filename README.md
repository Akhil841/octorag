# OctoRAG
Lightweight agent that uses GitHub Search API to do RAG for tasks such as recommending projects and libraries, and generating code with its selections. Written in Python using LangGraph.

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

## Usage
OctoRAG offers three different ways to run it:
- As a function call from a library that runs the tools it needs locally
- As a function call from a library that calls its tools from your MCP server
- As a command-line application that runs its tools locally

For all of these, you need a `.env` file which has a `ANTHROPIC_API_KEY` (for querying the model) and a `GH_ACCESS_TOKEN` (for browsing GitHub) set. Or, you must otherwise set them yourself before running.

### As a library, using local tools
Instantiate OctoRAG using the following:
```
from octorag.octorag import OctoRAG

model = OctoRAG("path/to/env/file") # Looks for a .env file in the root directory by default
```

And query the model using the `query` method:

```
model.query("I need an open-source raytracer for a bigger project I'm working on. It needs to be able to be called as a library, like I can just call a `raytrace()` function and it draws the input scene for me. I'm working in Rust. Give me a single up-to-date recommendations.")
```

### As a library, connecting to an MCP server

Your MCP server needs to have a `.env` file containing your `GH_ACCESS_TOKEN` (or otherwise have it set), and it must expose the tools implemented in `octorag_mcp_server.py`. If you are using a `.env` file, it must be in the same directory as the tools in that file. You can choose to either integrate the code in that file into your existing server workflow, or instantiate an MCP server with these tools by simply running the file.

OctoRAG has an inbuilt MCP client that connects the Anthropic model to the tools. So on your client device, you must have a `.env` file containing your `ANTHROPIC_API_KEY` before querying your MCP server. The client-side code should look like this.

```
from octorag.octorag_mcp_client import OctoRAG_MCP

model = OctoRAG_MCP(
    path_to_env_file = '/path/to/env/file/', # defaults to looking in root directory
    mcp_url = 'https://url.of.your.mcp.server.api' # defaults to https://localhost:8000/mcp 
) # instantiates model, ready for querying

await model.query("Give me a Balatro mod from GitHub to spice up my playthrough.")
```

The `OctoRAG_MCP.query` method returns an `AsyncGenerator` that iteratively returns all the messages the AI prints, as `str`s.

### As a command-line application
Install the OctoRag application using `pip install .` in the root directory. From there, you can query OctoRAG simply by entering `octorag` in the command line!
