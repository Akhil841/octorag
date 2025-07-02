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


class OctoRAG_MCP:
    class State(TypedDict):
        # Messages have the type "list". The `add_messages` function
        # in the annotation defines how this state key should be updated
        # (in this case, it appends messages to the list, rather than overwriting them)
        messages: Annotated[list, add_messages]

    def __init__(
        self, path_to_env_file: str = None, mcp_url: str = "http://localhost:8000/mcp"
    ):
        self.memory = MemorySaver()

        self.graph_builder = StateGraph(OctoRAG_MCP.State)

        from langchain.chat_models import init_chat_model

        self.llm = init_chat_model("anthropic:claude-3-7-sonnet-latest")

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
        self.llm = self.llm.bind_tools(tools)

        def llm_state(state: OctoRAG_MCP.State):
            return {"messages": [self.llm.invoke(state["messages"])]}

        self.graph_builder.add_node("llm", llm_state)

        self.graph_builder.add_edge(START, "llm")
        self.graph_builder.add_edge("llm", END)

        tool_node = ToolNode(tools=tools)
        self.graph_builder.add_node("tools", tool_node)

        self.graph_builder.add_conditional_edges(
            "llm", tools_condition, {"tools": "tools", END: END}
        )

        self.graph_builder.add_edge("tools", "llm")

        graph = self.graph_builder.compile(checkpointer=self.memory)

        return graph

    async def query(self, query: str):
        async with self.client.session("octorag-mcp") as session:
            graph = await self.create_graph(session)

            config = {"configurable": {"thread_id": "1"}, "recursion_limit": 100}

            async for message in graph.astream(
                {"messages": [{"role": "user", "content": query}]},
                config,
                stream_mode="values",
            ):
                if isinstance(message["messages"][-1], AIMessage):
                    if isinstance(message["messages"][-1].content, str):
                        yield message["messages"][-1].content
                    if "text" in message["messages"][-1].content[0]:
                        yield message["messages"][-1].content[0]["text"]
