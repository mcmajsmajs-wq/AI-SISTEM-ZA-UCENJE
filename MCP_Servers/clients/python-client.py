#!/usr/bin/env python3
"""
MCP Klijent Primer - Python
Zahteva: pip install mcp
"""

import asyncio
import os
from mcp import ClientSession, StdioClientTransport
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self, name: str, command: str, args: list = None, env: dict = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.session = None

    async def connect(self):
        env = {**os.environ, **self.env}
        transport = StdioClientTransport(
            command=self.command,
            args=self.args,
            env=env
        )
        async with stdio_client(transport) as (read, write):
            self.session = ClientSession(read, write)
            await self.session.initialize()
            print(f"✅ Povezan sa {self.name}")

    async def list_tools(self):
        if not self.session:
            raise RuntimeError("Niste povezani!")
        response = await self.session.list_tools()
        return response.tools

    async def call_tool(self, tool_name: str, arguments: dict = None):
        if not self.session:
            raise RuntimeError("Niste povezani!")
        return await self.session.call_tool(tool_name, arguments or {})

    async def list_prompts(self):
        if not self.session:
            raise RuntimeError("Niste povezani!")
        return await self.session.list_prompts()

    async def get_prompt(self, prompt_name: str, arguments: dict = None):
        if not self.session:
            raise RuntimeError("Niste povezani!")
        return await self.session.get_prompt(prompt_name, arguments or {})

    async def close(self):
        if self.session:
            await self.session.close()
            print(f"🔌 Isključen sa {self.name}")


async def main():
    print("=== MCP Python Klijent Demo ===\n")

    client = MCPClient(
        name="sequential-thinking",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
    )

    await client.connect()
    
    tools = await client.list_tools()
    print(f"\n📋 Alati ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool.name}")
    
    result = await client.call_tool(
        "sequentialthinking",
        {"thought": "Kako da napravim REST API?", "nextThoughtNeeded": True}
    )
    print(f"\n🧠 Rezultat: {result.content[0].text[:200]}...")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
