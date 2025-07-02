from octorag_mcp_client import OctoRAG_MCP
import asyncio

model = OctoRAG_MCP()


async def main():
    async for msg in model.query(
        "Give me a Balatro mod from GitHub to spice up my playthrough."
    ):
        print(msg)


q = asyncio.run(main())
