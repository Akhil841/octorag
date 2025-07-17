from octorag.octorag_mcp_client import OctoRAG_MCP
import asyncio

model = OctoRAG_MCP(debug=True)


async def main():
    async for msg in model.query(
        (
            "Write code in Rust for a raytracer. Use existing libraries from GitHub to handle the raytracing logic, I want a simple example that renders a sphere.",
        )
    ):
        print(msg)


q = asyncio.run(main())
