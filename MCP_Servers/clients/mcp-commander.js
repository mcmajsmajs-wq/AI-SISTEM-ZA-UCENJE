#!/usr/bin/env node
/**
 * MCP Commander - Interaktivni TUI za MCP servere
 * 
 * Usage: node mcp-commander.js
 */

const readline = require('readline');
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

const SERVERS = [
  { id: 'brave-search', name: '🌐 Brave Search', cmd: ['npx', '-y', '@modelcontextprotocol/server-brave-search'], env: 'BRAVE_API_KEY' },
  { id: 'sequential-thinking', name: '🧠 Sequential Thinking', cmd: ['npx', '-y', '@modelcontextprotocol/server-sequential-thinking'], env: null },
  { id: 'firecrawl', name: '🔥 Firecrawl', cmd: ['npx', '-y', 'firecrawl-mcp'], env: 'FIRECRAWL_API_KEY' },
  { id: 'docker', name: '🐳 Docker', cmd: ['npx', '-y', 'mcp-docker-server'], env: null },
  { id: 'github', name: '📦 GitHub', cmd: ['npx', '-y', '@modelcontextprotocol/server-github'], env: 'GITHUB_PERSONAL_ACCESS_TOKEN' },
  { id: 'gmail', name: '📧 Gmail', cmd: ['npx', '-y', '@gongrzhe/server-gmail-autoauth-mcp'], env: 'GMAIL_CLIENT_ID' },
];

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt) {
  return new Promise(resolve => rl.question(prompt, resolve));
}

function clear() {
  console.log('\x1B[2J\x1B[0f');
}

function header() {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║                    MCP Commander v1.0                       ║
║              Interaktivni MCP Server Manager               ║
╚══════════════════════════════════════════════════════════════╝
`);
}

async function listServers() {
  clear();
  header();
  console.log('📋 Dostupni MCP Serveri:\n');
  SERVERS.forEach((s, i) => {
    const hasEnv = s.env ? ` [${s.env}]` : '';
    console.log(`  ${i + 1}. ${s.name}${hasEnv}`);
  });
  console.log('\n  0. Izlaz\n');
}

async function connectToServer(server) {
  console.log(`\n🔌 Povezivanje sa ${server.name}...`);
  
  const env = { ...process.env };
  if (server.env) {
    env[server.env] = process.env[server.env] || '';
  }

  try {
    const transport = new StdioClientTransport({
      command: server.cmd[0],
      args: server.cmd.slice(1),
      env
    });

    const client = new Client({ name: `mcp-commander-${server.id}`, version: '1.0.0' });
    await client.connect(transport);
    
    console.log(`✅ Povezan sa ${server.name}!\n`);
    
    const tools = await client.listTools();
    console.log(`📋 Dostupni alati (${tools.tools.length}):\n`);
    tools.tools.forEach((t, i) => {
      console.log(`  ${i + 1}. ${t.name}`);
      if (t.description) console.log(`     ${t.description.substring(0, 50)}...`);
    });

    while (true) {
      console.log('\n┌─────────────────────────────────────┐');
      console.log('│ 1. Pozovi alat                     │');
      console.log('│ 2. Lista prompt-ovi                 │');
      console.log('│ 3. Odjava i povratak               │');
      console.log('└─────────────────────────────────────┘');
      
      const choice = await question('\n> ');
      
      if (choice === '1') {
        console.log('\nUnesite ime alata:');
        const toolName = await question('> ');
        
        console.log('Unesite argumente (JSON format, ili Enter za prazno):');
        const argsStr = await question('> ');
        
        let args = {};
        if (argsStr.trim()) {
          try { args = JSON.parse(argsStr); } catch { args = { input: argsStr }; }
        }
        
        try {
          const result = await client.callTool({ name: toolName, arguments: args });
          console.log('\n✅ Rezultat:');
          if (result.content) {
            result.content.forEach(c => console.log(c.text));
          }
        } catch (err) {
          console.log(`\n❌ Greška: ${err.message}`);
        }
      } 
      else if (choice === '2') {
        const prompts = await client.listPrompts();
        console.log('\n📝 Prompt-ovi:');
        prompts.prompts.forEach(p => console.log(`  - ${p.name}: ${p.description || 'N/A'}`));
      }
      else if (choice === '3') {
        await client.close();
        break;
      }
    }
  } catch (err) {
    console.log(`\n❌ Greška: ${err.message}`);
    if (err.message.includes('ENOENT') || err.message.includes('not found')) {
      console.log('💡 Server nije instaliran. Instalirajte sa:');
      console.log(`   npx ${server.cmd.slice(1).join(' ')}`);
    }
  }
}

async function main() {
  while (true) {
    await listServers();
    const choice = await question('Izaberi server (0-6): ');
    
    if (choice === '0') {
      console.log('\n👋 Poz!\n');
      rl.close();
      break;
    }
    
    const idx = parseInt(choice) - 1;
    if (idx >= 0 && idx < SERVERS.length) {
      await connectToServer(SERVERS[idx]);
    } else {
      console.log('\n❌ Nepravilan izbor!');
      await question('Pritisni Enter za nastavak...');
    }
  }
}

main().catch(console.error);
