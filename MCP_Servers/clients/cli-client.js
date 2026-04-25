#!/usr/bin/env node
/**
 * MCP CLI Klijent - Koristite iz terminala
 * 
 * Usage:
 *   node cli-client.js <server> <tool> [args...]
 * 
 * Primeri:
 *   node cli-client.js brave-search brave-web-search "MCP protocol"
 *   node cli-client.js sequential-thinking sequentialthinking "Optimizuj kod"
 *   node cli-client.js docker docker-ps
 * 
 * Serveri:
 *   brave-search, sequential-thinking, firecrawl, docker, github
 */

const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

const SERVERS = {
  'brave-search': {
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-brave-search'],
    env: () => ({ BRAVE_API_KEY: process.env.BRAVE_API_KEY || '' })
  },
  'sequential-thinking': {
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-sequential-thinking'],
    env: () => ({})
  },
  'firecrawl': {
    command: 'npx',
    args: ['-y', 'firecrawl-mcp'],
    env: () => ({ FIRECRAWL_API_KEY: process.env.FIRECRAWL_API_KEY || '' })
  },
  'docker': {
    command: 'npx',
    args: ['-y', 'mcp-docker-server'],
    env: () => ({})
  },
  'github': {
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-github'],
    env: () => ({ GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_PERSONAL_ACCESS_TOKEN || '' })
  },
  'gmail': {
    command: 'npx',
    args: ['-y', '@gongrzhe/server-gmail-autoauth-mcp'],
    env: () => ({
      GMAIL_CLIENT_ID: process.env.GMAIL_CLIENT_ID || '',
      GMAIL_CLIENT_SECRET: process.env.GMAIL_CLIENT_SECRET || ''
    })
  }
};

async function createClient(serverName) {
  const config = SERVERS[serverName];
  if (!config) {
    throw new Error(`Nepoznat server: ${serverName}. Dostupni: ${Object.keys(SERVERS).join(', ')}`);
  }

  const transport = new StdioClientTransport({
    command: config.command,
    args: config.args,
    env: { ...process.env, ...config.env() }
  });

  const client = new Client({
    name: `mcp-cli-${serverName}`,
    version: '1.0.0'
  }, { capabilities: {} });

  await client.connect(transport);
  return client;
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args[0] === '--help') {
    console.log(`
╔═══════════════════════════════════════════════════════╗
║              MCP CLI Klijent                          ║
╠═══════════════════════════════════════════════════════╣
║ Usage: node cli-client.js <server> <command> [args]   ║
╠═══════════════════════════════════════════════════════╣
║ Serveri:                                             ║
║   brave-search      - Web pretraga                    ║
║   sequential-thinking - Strukturalno razmisljanje     ║
║   firecrawl         - Web scraping                   ║
║   docker            - Docker upravljanje             ║
║   github            - GitHub integracija             ║
║   gmail             - Gmail integracija              ║
╠═══════════════════════════════════════════════════════╣
║ Primeri:                                              ║
║   node cli-client.js brave-search brave-web-search "MCP" ║
║   node cli-client.js sequential-thinking sequentialthinking "Problem..." ║
║   node cli-client.js docker docker-ps                 ║
║   node cli-client.js github list-repos                ║
╠═══════════════════════════════════════════════════════╣
║ Opcije:                                               ║
║   --help          - Prikazi pomoc                     ║
║   --list          - Lista alate za server             ║
║   --prompts       - Lista prompt-ove za server        ║
╚═══════════════════════════════════════════════════════╝
`);
    process.exit(0);
  }

  const serverName = args[0];

  if (args[1] === '--list') {
    const client = await createClient(serverName);
    const tools = await client.listTools();
    console.log(`\n📋 Alati za ${serverName}:\n`);
    tools.tools.forEach(t => {
      console.log(`  ${t.name}`);
      if (t.description) console.log(`    ${t.description.substring(0, 60)}...`);
    });
    await client.close();
    return;
  }

  if (args[1] === '--prompts') {
    const client = await createClient(serverName);
    const prompts = await client.listPrompts();
    console.log(`\n💬 Prompt-ovi za ${serverName}:\n`);
    prompts.prompts.forEach(p => {
      console.log(`  ${p.name}`);
      if (p.description) console.log(`    ${p.description}`);
    });
    await client.close();
    return;
  }

  const toolName = args[1];
  const toolArgs = args.slice(2);

  console.log(`🔄 Pokretanje: ${serverName}/${toolName}`);
  
  const client = await createClient(serverName);
  
  let parsedArgs = {};
  if (toolArgs.length > 0) {
    try {
      parsedArgs = JSON.parse(toolArgs.join(' '));
    } catch {
      parsedArgs = { query: toolArgs.join(' ') };
    }
  }

  try {
    const result = await client.callTool({
      name: toolName,
      arguments: parsedArgs
    });
    
    console.log('\n✅ Rezultat:\n');
    if (result.content) {
      result.content.forEach(c => {
        console.log(c.text || JSON.stringify(c, null, 2));
      });
    } else {
      console.log(JSON.stringify(result, null, 2));
    }
  } catch (error) {
    console.error('❌ Greška:', error.message);
    process.exit(1);
  }

  await client.close();
}

main().catch(err => {
  console.error('❌ Fatalna greška:', err.message);
  process.exit(1);
});
