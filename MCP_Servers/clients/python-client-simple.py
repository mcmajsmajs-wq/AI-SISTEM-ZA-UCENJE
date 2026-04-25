#!/usr/bin/env python3
"""
MCP Klijent - Python verzija
Napomena: Zahteva instalaciju: pip install mcp
Ako imate problema sa pip, koristite Docker verziju dole.
"""

import asyncio
import os


class MCPClient:
    """Jednostavni MCP klijent za povezivanje sa MCP serverima"""
    
    def __init__(self, name: str, server_command: list, env: dict = None):
        self.name = name
        self.server_command = server_command
        self.env = env or {}
        self.session = None

    async def connect(self):
        try:
            from mcp import ClientSession, StdioClientTransport
        except ImportError:
            print("⚠️ MCP paket nije instaliran. Instalirajte sa: pip install mcp")
            print("Ili koristite Docker klijent (pogledajte docker-client.py)")
            return

        from mcp.client.stdio import stdio_client
        
        full_env = {**os.environ, **self.env}
        
        async with stdio_client(
            StdioClientTransport(
                command=self.server_command[0],
                args=self.server_command[1:],
                env=full_env
            )
        ) as (read, write):
            self.session = ClientSession(read, write)
            await self.session.initialize()
            print(f"✅ Povezan sa {self.name}")

    async def list_tools(self):
        if not self.session:
            raise RuntimeError("Niste povezani!")
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, arguments: dict = None):
        if not self.session:
            raise RuntimeError("Niste povezani!")
        result = await self.session.call_tool(tool_name, arguments or {})
        return result

    async def close(self):
        if self.session:
            await self.session.close()


async def example_usage():
    client = MCPClient(
        name="brave-search",
        server_command=["npx", "-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")}
    )
    
    await client.connect()
    
    tools = await client.list_tools()
    print(f"Alati: {[t.name for t in tools]}")
    
    result = await client.call_tool("brave-search", {"query": "MCP protocol"})
    print(f"Rezultat: {result}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
