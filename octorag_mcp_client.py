from dotenv import load_dotenv

from typing import Annotated

from typing_extensions import TypedDict

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langgraph.prebuilt import ToolNode, tools_condition

from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages.ai import AIMessage

from langchain_core.messages.human import HumanMessage


class OctoRAG_MCP:
    class State(TypedDict):
        # Messages have the type "list". The `add_messages` function
        # in the annotation defines how this state key should be updated
        # (in this case, it appends messages to the list, rather than overwriting them)
        messages: Annotated[list, add_messages]
        current_agent: str | None

    def __init__(
        self, path_to_env_file: str = None, mcp_url: str = "http://localhost:8000/mcp"
    ):
        self.memory = MemorySaver()

        self.graph_builder = StateGraph(OctoRAG_MCP.State)

        from langchain.chat_models import init_chat_model

        self.agent1_raw = init_chat_model("anthropic:claude-3-7-sonnet-latest")
        self.agent1_name = "Repository Retriever"
        self.agent1_system_prompt = (
            "You are the Repository Retriever agent."
            "You are a helpful assistant that has the capability to browse GitHub repositories and provide information about them. "
            "You will be provided a query and you should respond with relevant GitHub repositories"
            " and their details. Make sure to compare the user's use case against the repository's licensing to ensure the user can use the code in the repository."
            "You MUST use the query_for_github_repos tool to retrieve information about repositories from GitHub based on natural language keywords. Do NOT solely rely on your own knowledge, you NEED to provide up-to-date recommendations."
            "If the query you have is unrelated to GitHub, you may finish as soon as you respond. Otherwise, send the repositories you have found as well as your query to the Repository Curator."
            "You MUST send your work to the Repository Curator once you are done. Only end the conversation if the query is unrelated to GitHub or if you have no repositories to send. You can send your work by mentioning the Repository Curator in your response."
            "You ONLY retrieve repositories, you do NOT do further work on them yourself. Send your work to the Repository Curator for further processing."
            "When passing the repositories to the Repository Curator, you MUST list all the GitHub repositories you found, and repeat the query. You MUST phrase it as an action the Code Generator should take, such as 'Please curate these repositories [repositories] based on the query: [query]'."
            "If you receive a request for more repositories from the Repository Curator, you MUST search for more repositories based on what it asks and send them back to the Repository Curator."
            "Indicate that you want to end the conversation by saying <<END>>. THIS WILL END THE CONVERSATION FULLY AND NOT HAND YOUR WORK TO THE REPOSITORY CURATOR."
        )
        self.agent2_raw = init_chat_model("anthropic:claude-3-7-sonnet-latest")
        self.agent2_name = "Repository Curator"
        self.agent2_system_prompt = (
            "You are the Repository Curator agent."
            "You are a helpful assistant that can take a list of GitHub repositories, as well as a query, and curate which repositories are most relevant to the query. "
            "You may communicate with the Repository Retriever to get more repositories if needed, if you deem the ones you have to be insufficient. "
            "Once you are satisfied with the repositories you have, you may either return your message to the user and finish, or ask the Code Generator to generate code from the repositories, if"
            " the user has requested it. "
            "Use the get_readme tool to get the README file of a repository."
            "You MUST use the tools provided to you to learn more about the repositories and curate them. Do NOT solely rely on your own knowledge, you NEED to provide up-to-date recommendations."
            "Once you have finished your preliminary work, you MUST either ask the Repository Retriever to get more repositories to get better results, or ask the Code Generator to generate code based on the repositories you have."
            "DO NOT GENERATE ANY CODE YOURSELF, YOU MUST PASS THE REPOSITORIES TO THE CODE GENERATOR FOR FURTHER PROCESSING."
            "You can ask the Repository Retriever to get more repositories by mentioning the Repository Retriever in your response, and you can send your work to the Code Generator by mentioning the Code Generator in your response."
            "ONLY end the conversation if the prompt is unrelated to GitHub, or if you have no repositories to curate."
            "You ONLY curate repositories, you do NOT generate code yourself. Send your work to the Code Generator for further processing."
            "When asking the Repository Retriever to get more repositories, you MUST phrase it as an action the Repository Retriever should take, such as 'Please retrieve more repositories based on the query: [query]'. Also include extra information you need if necessary."
            "When finally passing the repositories to the Code Generator, you MUST list all the GitHub repositories you think it will need for code generation, and repeat the query. You MUST phrase it as an action the Code Generator should take, such as 'Please generate code based on these repositories [repositories] and the query: [query]'."
            "Indicate that you want to end the conversation by saying <<END>>. THIS WILL END THE CONVERSATION FULLY AND NOT HAND YOUR WORK OVER TO ANOTHER AGENT."
        )
        self.agent3_raw = init_chat_model("anthropic:claude-3-7-sonnet-latest")
        self.agent3_name = "Code Generator"
        self.agent3_system_prompt = (
            "You are the Code Generator agent."
            "You are a helpful assistant that can take a list of GitHub repositories, as well as a query, and generate code based on the repositories. "
            "You have tools that can generate a file tree of an existing repository, as well as read files from a repository. Use these tools to write proper code based on the repositories and the query. "
            "Use the get_repo_tree tool to get the file tree of a repository, and the get_file_contents tool to read files from a repository."
            "Use the get_readme tool to get the README file of a repository."
            "PRIMARILY use get_readme to understand how to use the repository. As in, avoid reading other files in the repositories if possible. Only use the other tools if you REALLY need to read files other than the README file."  # don't we all love rate limits?
            "You MUST use the tools provided to you to learn more about the repositories and generate code. Do NOT solely rely on your own knowledge, you NEED to read through the repositories to understand how to use them."
            "Once you are satisfied with the code you have generated, you MUST send your work to the Code Poster. Only end the conversation if the prompt is unrelated to GitHub."
            "You MUST indicate that you want to send the code to the Code Poster by mentioning the Code Poster in your response."
            "You ONLY generate code, you do NOT publish them yourself. Send your work to the Code Poster for further processing."
            "When passing the code to the Code Poster, you MUST write out each file's name and its contents, and phrase it as an action the Code Poster should take, such as 'Please upload these files to a new GitHub repository: [file1_name]: [file1_contents], [file2_name]: [file2_contents], ...'."
            "Indicate that you want to end the conversation by saying <<END>>. THIS WILL END THE CONVERSATION FULLY AND NOT HAND YOUR WORK OVER TO THE CODE POSTER."
        )
        self.agent4_raw = init_chat_model("anthropic:claude-3-7-sonnet-latest")
        self.agent4_name = "Code Poster"
        self.agent4_system_prompt = (
            "You are the Code Poster agent."
            "You are a helpful assistant that can take in code snippets and upload them to a new GitHub repository."
            "Use the create_repo tool to create a new repository, and the create_file tool to upload files to the repository. Only upload 150 characters at a time to a file to avoid rate limits."
            "You may use the `append_to_file` tool to append to files if the file is too large to upload in one go (longer than 150 characters)."
            "Use these tools to create a new repository and upload the code snippets you have been given."
            "The contents of each file, as well as their names, are in the previous messages. For each file, pass the first 150 characters of the file contents as well as the name of the file to the create_file tool."
            "Pass subsequent batches of 150 characters of the file contents to the append_to_file tool, until the entire file is uploaded."
            "For example, let's say the repository is at `github.com/my-account/my-repo`, and you want to create a file named `code.py` which contains `print('Hello, world!')`. You would call the create_file tool"
            " as follows: create_file(owner='my_account', repo='my-repo', file_contents='print('Hello, world!')', filename='code.py'). "
            "You MUST use the create_repo tool to create a new repository, and you MUST upload all the code files you have been given to the repository using the create_file and append_to_file tools."
            "Indicate that you want to end the conversation by saying <<END>>. THIS WILL END THE CONVERSATION FULLY AND NOT ALLOW YOU TO TAKE ANY MORE ACTIONS TO POST THE CODE."
        )
        self.agent_names = [
            None,
            self.agent1_name,
            self.agent2_name,
            self.agent3_name,
            self.agent4_name,
        ]
        self.system_prompts = [
            None,
            self.agent1_system_prompt,
            self.agent2_system_prompt,
            self.agent3_system_prompt,
            self.agent4_system_prompt,
        ]

        load_dotenv(path_to_env_file)

        self.client = MultiServerMCPClient(
            {
                "octorag-mcp": {
                    "url": mcp_url,
                    "transport": "streamable_http",
                }
            }
        )

    async def create_graph(self, session):
        tools = await load_mcp_tools(session)
        print(len(tools), "tools loaded")

        # Give all agents only the tools they are allowed to use.
        self.agent1 = self.agent1_raw.bind_tools([tools[1]])
        self.agent2 = self.agent2_raw.bind_tools([tools[0]])
        self.agent3 = self.agent3_raw.bind_tools([tools[0], tools[2], tools[3]])
        self.agent4 = self.agent4_raw.bind_tools(tools[4:])

        self.agent1.name = self.agent1_name
        self.agent2.name = self.agent2_name
        self.agent3.name = self.agent3_name
        self.agent4.name = self.agent4_name

        self.agents = [None, self.agent1, self.agent2, self.agent3, self.agent4]

        def agent1_state(state: OctoRAG_MCP.State):
            system_message = {
                "role": "system",
                "content": self.system_prompts[1],
            }
            # Only prepend system message for the model call, not for storage
            prompt_messages = [system_message] + state["messages"]
            ai_message = self.agents[1].invoke(prompt_messages)
            return {
                "messages": state["messages"] + [ai_message],
                "current_agent": "agent1",
            }

        def agent2_state(state: OctoRAG_MCP.State):
            system_message = {
                "role": "system",
                "content": self.system_prompts[2],
            }
            prompt_messages = [system_message] + state["messages"]
            ai_message = self.agents[2].invoke(prompt_messages)
            return {
                "messages": state["messages"] + [ai_message],
                "current_agent": "agent2",
            }

        def agent3_state(state: OctoRAG_MCP.State):
            system_message = {
                "role": "system",
                "content": self.system_prompts[3],
            }
            prompt_messages = [system_message] + state["messages"]
            ai_message = self.agents[3].invoke(prompt_messages)
            return {
                "messages": state["messages"] + [ai_message],
                "current_agent": "agent3",
            }

        def agent4_state(state: OctoRAG_MCP.State):
            system_message = {
                "role": "system",
                "content": self.system_prompts[4],
            }
            prompt_messages = [system_message] + state["messages"]
            ai_message = self.agents[4].invoke(prompt_messages)
            return {
                "messages": state["messages"] + [ai_message],
                "current_agent": "agent4",
            }

        self.graph_builder.add_node(self.agent_names[1], agent1_state)
        self.graph_builder.add_node(self.agent_names[2], agent2_state)
        self.graph_builder.add_node(self.agent_names[3], agent3_state)
        self.graph_builder.add_node(self.agent_names[4], agent4_state)

        self.graph_builder.add_edge(START, self.agent_names[1])

        def orchestrator_state(state: OctoRAG_MCP.State):
            return {
                "messages": state["messages"],
                "current_agent": state["current_agent"],
            }

        self.graph_builder.add_node("orchestrator", orchestrator_state)

        def mentions_agent(content, agent_name):
            agent_name = agent_name.lower()
            if isinstance(content, str):
                return (
                    agent_name in content.lower() or f"@{agent_name}" in content.lower()
                )
            elif isinstance(content, list):
                return any(
                    agent_name
                    in (
                        item.get("text", "").lower()
                        if isinstance(item, dict)
                        else str(item).lower()
                    )
                    or f"@{agent_name}"
                    in (
                        item.get("text", "").lower()
                        if isinstance(item, dict)
                        else str(item).lower()
                    )
                    for item in content
                )
            return False

        def mentions_end(content):
            if isinstance(content, str):
                return "<<end>>" in content.lower()
            elif isinstance(content, list):
                return any(
                    "<<end>>"
                    in (
                        item.get("text", "").lower()
                        if isinstance(item, dict)
                        else str(item).lower()
                    )
                    for item in content
                )
            return False

        def orchestrator_routing(state: OctoRAG_MCP.State):
            if isinstance(state, list):
                ai_message = state[-1]
            elif messages := state.get("messages"):
                ai_message = messages[-1]
            else:
                raise ValueError(
                    f"No messages found in input state to tool_edge: {state}"
                )
            print(
                f"Current agent: {state['current_agent']}, tool_calls: {getattr(ai_message, 'tool_calls', None)} content: {ai_message.content if hasattr(ai_message, 'content') else None}"
            )
            if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
                return state["current_agent"] + "_tools"
            content = ai_message.content
            # Agent 1 may use its tools to retrieve repositories, refine the response by asking agent 2, or finish the conversation
            if state["current_agent"] == "agent1":
                if mentions_agent(content, self.agent_names[2]):
                    state["current_agent"] = "agent2"
                    state["messages"].append(HumanMessage(content=content))
                    return "agent2"
                if mentions_end(content):
                    return END
                return "agent1"
            # Agent 2 may use its tools to curate repositories, get more repositories from agent 1, ask agent 3 to generate code, or finish the conversation
            elif state["current_agent"] == "agent2":
                if mentions_agent(content, self.agent_names[1]):
                    state["current_agent"] = "agent1"
                    state["messages"].append(HumanMessage(content=content))
                    return "agent1"
                if mentions_agent(content, self.agent_names[3]):
                    state["current_agent"] = "agent3"
                    state["messages"].append(HumanMessage(content=content))
                    return "agent3"
                if mentions_end(content):
                    return END
                return "agent2"
            # Agent 3 may use its tools to generate code, ask agent 4 to post the code, or finish the conversation
            elif state["current_agent"] == "agent3":
                if mentions_agent(content, self.agent_names[4]):
                    state["current_agent"] = "agent4"
                    state["messages"].append(HumanMessage(content=content))
                    return "agent4"
                if mentions_end(content):
                    return END
                return "agent3"
            # Agent 4 may use its tools to create a repository and upload files, or finish the conversation
            elif state["current_agent"] == "agent4":
                if mentions_end(content):
                    return END
                return "agent4"
            return END

        agent1_tools = ToolNode(tools=[tools[1]])
        self.graph_builder.add_node("agent1_tools", agent1_tools)
        self.graph_builder.add_edge(self.agent_names[1], "orchestrator")
        self.graph_builder.add_edge("agent1_tools", self.agent_names[1])

        agent2_tools = ToolNode(tools=[tools[0]])
        self.graph_builder.add_node("agent2_tools", agent2_tools)
        self.graph_builder.add_edge(self.agent_names[2], "orchestrator")
        self.graph_builder.add_edge("agent2_tools", self.agent_names[2])

        agent3_tools = ToolNode(tools=[tools[0], tools[2], tools[3]])
        self.graph_builder.add_node("agent3_tools", agent3_tools)
        self.graph_builder.add_edge(self.agent_names[3], "orchestrator")
        self.graph_builder.add_edge("agent3_tools", self.agent_names[3])

        agent4_tools = ToolNode(tools=tools[4:])
        self.graph_builder.add_node("agent4_tools", agent4_tools)
        self.graph_builder.add_edge(self.agent_names[4], "orchestrator")
        self.graph_builder.add_edge("agent4_tools", self.agent_names[4])

        self.graph_builder.add_conditional_edges(
            "orchestrator",
            orchestrator_routing,
            {
                "agent1": self.agent_names[1],
                "agent2": self.agent_names[2],
                "agent3": self.agent_names[3],
                "agent4": self.agent_names[4],
                "agent1_tools": "agent1_tools",
                "agent2_tools": "agent2_tools",
                "agent3_tools": "agent3_tools",
                "agent4_tools": "agent4_tools",
                END: END,
            },
        )

        graph = self.graph_builder.compile(checkpointer=self.memory)

        return graph

    async def query(self, query: str):
        async with self.client.session("octorag-mcp") as session:
            graph = await self.create_graph(session)

            config = {"configurable": {"thread_id": "1"}, "recursion_limit": 10000}

            async for message in graph.astream(
                {"messages": [{"role": "user", "content": query}]},
                config,
                stream_mode="values",
            ):
                if isinstance(message["messages"][-1], AIMessage):
                    content = message["messages"][-1].content
                    if isinstance(content, str):
                        yield content
                    elif (
                        isinstance(content, list)
                        and len(content) > 0
                        and "text" in content[-1]
                    ):
                        yield content[-1]["text"]
