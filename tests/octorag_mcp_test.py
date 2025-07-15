from octorag.octorag_mcp_client import OctoRAG_MCP
import asyncio

model = OctoRAG_MCP()


async def main():
    async for msg in model.query(
        (
            "Write code in Python to create a HTTP server that can handle GET and POST requests"
            " It should be able to retrieve stats of NBA players from the NBA API when asked."
            " And it should predict the probability of a team winning a game against another team, based on the stats of the players."
        )
    ):
        print(msg)


q = asyncio.run(main())
