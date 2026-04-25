/**
 * MCP REST API Server
 * Izlozi MCP servere kao REST API
 * 
 * Usage:
 *   node rest-api-server.js [port]
 * 
 * Endpoints:
 *   GET  /servers              - Lista svih povezanih servera
 *   GET  /servers/:name/tools - Lista alata za server
 *   POST /servers/:name/call   - Pozovi alat
 *   GET  /servers/:name/prompts - Lista prompt-ova
 */

const http = require('http');
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

const PORT = process.env.PORT || 3000;
const connectedServers = new Map();

const SERVERS_CONFIG = {
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
  }
};

async function connectServer(name) {
  if (connectedServers.has(name)) {
    return connectedServers.get(name);
  }

  const config = SERVERS_CONFIG[name];
  if (!config) {
    throw new Error(`Nepoznat server: ${name}`);
  }

  const transport = new StdioClientTransport({
    command: config.command,
    args: config.args,
    env: { ...process.env, ...config.env() }
  });

  const client = new Client({ name: `mcp-rest-${name}`, version: '1.0.0' }, { capabilities: {} });
  await client.connect(transport);
  
  connectedServers.set(name, client);
  console.log(`✅ Povezan: ${name}`);
  return client;
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        resolve({});
      }
    });
    req.on('error', reject);
  });
}

async function handleRequest(req, res) {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  try {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const path = url.pathname;

    if (path === '/servers' && req.method === 'GET') {
      res.writeHead(200);
      res.end(JSON.stringify({
        servers: Object.keys(SERVERS_CONFIG),
        connected: Array.from(connectedServers.keys())
      }));
      return;
    }

    const serverMatch = path.match(/^\/servers\/([^/]+)\/tools$/);
    if (serverMatch && req.method === 'GET') {
      const serverName = serverMatch[1];
      const client = await connectServer(serverName);
      const tools = await client.listTools();
      res.writeHead(200);
      res.end(JSON.stringify({ tools: tools.tools }));
      return;
    }

    const promptMatch = path.match(/^\/servers\/([^/]+)\/prompts$/);
    if (promptMatch && req.method === 'GET') {
      const serverName = promptMatch[1];
      const client = await connectServer(serverName);
      const prompts = await client.listPrompts();
      res.writeHead(200);
      res.end(JSON.stringify({ prompts: prompts.prompts }));
      return;
    }

    const callMatch = path.match(/^\/servers\/([^/]+)\/call$/);
    if (callMatch && req.method === 'POST') {
      const serverName = callMatch[1];
      const body = await parseBody(req);
      
      if (!body.tool || !body.arguments) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'Ocekivano: { tool: "ime", arguments: {} }' }));
        return;
      }

      const client = await connectServer(serverName);
      const result = await client.callTool({
        name: body.tool,
        arguments: body.arguments
      });

      res.writeHead(200);
      res.end(JSON.stringify({ result }));
      return;
    }

    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not Found' }));
  } catch (error) {
    res.writeHead(500);
    res.end(JSON.stringify({ error: error.message }));
  }
}

async function main() {
  console.log('╔════════════════════════════════════════╗');
  console.log('║     MCP REST API Server               ║');
  console.log('╚════════════════════════════════════════╝\n');
  
  const server = http.createServer(handleRequest);
  
  server.listen(PORT, () => {
    console.log(`🚀 Server pokrenut na http://localhost:${PORT}`);
    console.log('\nEndpoints:');
    console.log('  GET  /servers                   - Lista servera');
    console.log('  GET  /servers/:name/tools        - Lista alata');
    console.log('  GET  /servers/:name/prompts      - Lista prompt-ova');
    console.log('  POST /servers/:name/call         - Pozovi alat');
    console.log('\nPrimer poziva:');
    console.log(`curl -X POST http://localhost:${PORT}/servers/brave-search/call \\`);
    console.log('  -H "Content-Type: application/json" \\');
    console.log('  -d \'{"tool": "brave-web-search", "arguments": {"query": "MCP"}}\'');
  });
}

main();
