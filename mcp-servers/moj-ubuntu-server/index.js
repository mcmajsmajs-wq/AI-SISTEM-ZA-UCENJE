import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";

const server = new Server({
  name: "moj-ubuntu-server",
  version: "1.0.0",
}, {
  capabilities: { tools: {} },
});

// Definisanje dostupnih alata
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "proveri_sistem",
    description: "Vraća zauzeće diska i memorije na Ubuntu sistemu",
    inputSchema: { type: "object", properties: {} }
  }]
}));

// Logika alata
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "proveri_sistem") {
    const disk = execSync("df -h /").toString();
    const mem = execSync("free -h").toString();
    return {
      content: [{ type: "text", text: `Disk:\n${disk}\nMemorija:\n${mem}` }]
    };
  }
  throw new Error("Alat nije pronađen");
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("Moj Ubuntu MCP Server je pokrenut!");
