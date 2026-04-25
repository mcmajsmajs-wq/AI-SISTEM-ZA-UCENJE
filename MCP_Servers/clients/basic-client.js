const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

async function createMCPClient(serverCommand, serverArgs = []) {
  const transport = new StdioClientTransport({
    command: serverCommand,
    args: serverArgs,
  });

  const client = new Client({
    name: 'mcp-example-client',
    version: '1.0.0',
  }, {
    capabilities: {},
  });

  await client.connect(transport);
  return client;
}

async function main() {
  console.log('=== MCP Klijent Primer ===\n');

  const client = await createMCPClient('npx', ['-y', '@modelcontextprotocol/server-sequential-thinking']);

  try {
    const tools = await client.listTools();
    console.log('Dostupni alati:', tools.tools.map(t => t.name));

    const prompts = await client.listPrompts();
    console.log('Dostupni prompt-ovi:', prompts.prompts.map(p => p.name));

    const resources = await client.listResources();
    console.log('Dostupni resursi:', resources.resources.map(r => r.uri));

  } catch (error) {
    console.error('Greška:', error.message);
  } finally {
    await client.close();
  }
}

main();
