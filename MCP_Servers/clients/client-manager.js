const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

class MCPClientManager {
  constructor() {
    this.clients = new Map();
  }

  async connect(name, command, args = [], env = {}) {
    try {
      const transport = new StdioClientTransport({
        command,
        args,
        env: { ...process.env, ...env }
      });

      const client = new Client({
        name: `mcp-client-${name}`,
        version: '1.0.0',
      }, { capabilities: {} });

      await client.connect(transport);
      this.clients.set(name, { client, transport });
      console.log(`✅ Povezan sa ${name}`);
      return client;
    } catch (error) {
      console.error(`❌ Greška povezivanja sa ${name}:`, error.message);
      throw error;
    }
  }

  async disconnect(name) {
    const connection = this.clients.get(name);
    if (connection) {
      await connection.client.close();
      this.clients.delete(name);
      console.log(`🔌 Isključen sa ${name}`);
    }
  }

  async callTool(serverName, toolName, args = {}) {
    const connection = this.clients.get(serverName);
    if (!connection) {
      throw new Error(`Server ${serverName} nije povezan`);
    }
    return await connection.client.callTool({ name: toolName, arguments: args });
  }

  async listTools(serverName) {
    const connection = this.clients.get(serverName);
    if (!connection) throw new Error(`Server ${serverName} nije povezan`);
    return await connection.client.listTools();
  }

  async listPrompts(serverName) {
    const connection = this.clients.get(serverName);
    if (!connection) throw new Error(`Server ${serverName} nije povezan`);
    return await connection.client.listPrompts();
  }

  async getPrompt(serverName, promptName, args = {}) {
    const connection = this.clients.get(serverName);
    if (!connection) throw new Error(`Server ${serverName} nije povezan`);
    return await connection.client.getPrompt({ name: promptName, arguments: args });
  }

  async readResource(serverName, uri) {
    const connection = this.clients.get(serverName);
    if (!connection) throw new Error(`Server ${serverName} nije povezan`);
    return await connection.client.readResource({ uri });
  }

  getConnectedServers() {
    return Array.from(this.clients.keys());
  }
}

async function demo() {
  const manager = new MCPClientManager();

  console.log('=== MCP Client Manager Demo ===\n');

  await manager.connect('sequential-thinking', 'npx', ['-y', '@modelcontextprotocol/server-sequential-thinking']);

  const tools = await manager.listTools('sequential-thinking');
  console.log('\n📋 Alati dostupni na sequential-thinking:');
  tools.tools.forEach(t => console.log(`  - ${t.name}: ${t.description}`));

  const result = await manager.callTool('sequential-thinking', 'sequentialthinking', {
    thought: 'Kako da optimizujem ovaj kod?',
    nextThoughtNeeded: true
  });
  console.log('\n🧠 Rezultat razmišljanja:', result.content[0].text);

  await manager.disconnect('sequential-thinking');
}

demo().catch(console.error);
