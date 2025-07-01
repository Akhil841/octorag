from dotenv import load_dotenv

from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langgraph.prebuilt import ToolNode, tools_condition

from langgraph.checkpoint.memory import MemorySaver


class OctoRAG:
    def __init__(self, path_to_env_file=None):
        class State(TypedDict):
            # Messages have the type "list". The `add_messages` function
            # in the annotation defines how this state key should be updated
            # (in this case, it appends messages to the list, rather than overwriting them)
            messages: Annotated[list, add_messages]

        memory = MemorySaver()

        graph_builder = StateGraph(State)

        from langchain.chat_models import init_chat_model

        llm = init_chat_model("anthropic:claude-3-7-sonnet-latest")

        def llm_state(state: State):
            return {"messages": [llm.invoke(state["messages"])]}

        load_dotenv(path_to_env_file)

        from octorag_tools import (
            query_for_github_repos,
            get_readme,
            get_repo_tree,
            get_file_contents,
        )

        tools = [query_for_github_repos, get_readme, get_repo_tree, get_file_contents]

        llm = llm.bind_tools(tools)

        # The first argument is the unique node name
        # The second argument is the function or object that will be called whenever
        # the node is used.
        graph_builder.add_node("llm", llm_state)

        graph_builder.add_edge(START, "llm")
        graph_builder.add_edge("llm", END)

        tool_node = ToolNode(tools=tools)
        graph_builder.add_node("tools", tool_node)

        graph_builder.add_conditional_edges(
            "llm", tools_condition, {"tools": "tools", END: END}
        )

        graph_builder.add_edge("tools", "llm")

        self.graph = graph_builder.compile(checkpointer=memory)

        self.config = {"configurable": {"thread_id": "1"}, "recursion_limit": 100}

    def query(self, query: str):
        events = self.graph.stream(
            {"messages": [{"role": "user", "content": query}]},
            self.config,
            stream_mode="values",
        )

        # Force run to finish before printing responses
        all_events = list(events)

        return all_events[-1]["messages"][-1].content
