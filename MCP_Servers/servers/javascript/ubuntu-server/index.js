import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ListPromptsRequestSchema,
  ReadResourceRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { execSync, exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

const server = new Server(
  {
    name: "moj-ubuntu-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {
        listChanged: true,
      },
      resources: {
        subscribe: true,
        listChanged: true,
      },
      prompts: {
        listChanged: true,
      },
    },
  }
);

const PROJECT_INFO = {
  name: "Ubuntu System Monitor",
  description: "MCP Server for monitoring Ubuntu system resources",
  version: "1.0.0",
};

const TOOLS = [
  {
    name: "proveri_sistem",
    description: "Vraća zauzeće diska i memorije na Ubuntu sistemu",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "proveri_cpu",
    description: "Vraća informacije o CPU usage i procesima",
    inputSchema: {
      type: "object",
      properties: {
        top: {
          type: "number",
          description: "Broj top procesa za prikaz (default: 10)",
          default: 10,
        },
      },
      required: [],
    },
  },
  {
    name: "proveri_mrezu",
    description: "Vraća mrežne statistike i aktivne konekcije",
    inputSchema: {
      type: "object",
      properties: {
        detailed: {
          type: "boolean",
          description: "Prikaži detaljne informacije",
          default: false,
        },
      },
      required: [],
    },
  },
  {
    name: "proveri_disk",
    description: "Vraća detaljne informacije o diskovima i particijama",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "proveri_procese",
    description: "Vraća listu aktivnih procesa",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Broj procesa za prikaz (default: 20)",
          default: 20,
        },
        sortBy: {
          type: "string",
          description: "Sortiraj po: cpu, memory (default: cpu)",
          enum: ["cpu", "memory"],
          default: "cpu",
        },
      },
      required: [],
    },
  },
];

const RESOURCES = [
  {
    uri: "system://cpu",
    name: "CPU Info",
    mimeType: "application/json",
    description: "CPU information and current usage",
  },
  {
    uri: "system://memory",
    name: "Memory Info",
    mimeType: "application/json",
    description: "Memory usage information",
  },
  {
    uri: "system://disk",
    name: "Disk Info",
    mimeType: "application/json",
    description: "Disk space and partition information",
  },
  {
    uri: "system://network",
    name: "Network Info",
    mimeType: "application/json",
    description: "Network interfaces and statistics",
  },
  {
    uri: "system://uptime",
    name: "System Uptime",
    mimeType: "text/plain",
    description: "System uptime information",
  },
  {
    uri: "system://hostname",
    name: "Hostname",
    mimeType: "text/plain",
    description: "System hostname",
  },
];

const PROMPTS = [
  {
    name: "system-analysis",
    description: "Analyze the complete system status and provide recommendations",
    arguments: [
      {
        name: "focus",
        description: "Focus area: performance, storage, network, or all (default: all)",
        required: false,
      },
    ],
  },
  {
    name: "resource-report",
    description: "Generate a detailed resource usage report",
    arguments: [
      {
        name: "timeframe",
        description: "Timeframe: current, 1hour, 24hours (default: current)",
        required: false,
      },
    ],
  },
  {
    name: "troubleshoot-performance",
    description: "Troubleshoot system performance issues",
    arguments: [
      {
        name: "symptom",
        description: "Symptom: slow, high-cpu, high-memory, high-disk",
        required: true,
      },
    ],
  },
];

async function runCommand(command) {
  try {
    const { stdout, stderr } = await execAsync(command, { timeout: 10000 });
    return { success: true, stdout: stdout.trim(), stderr: stderr.trim() };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

function parseMemoryInfo() {
  try {
    const output = execSync("free -b").toString();
    const lines = output.split("\n");
    const memLine = lines[1].split(/\s+/);
    const memTotal = parseInt(memLine[1]);
    const memUsed = parseInt(memLine[2]);
    const memFree = parseInt(memLine[3]);
    const memBuffers = parseInt(memLine[5]);
    const memAvailable = parseInt(memLine[6]);

    return {
      total: memTotal,
      used: memUsed,
      free: memFree,
      buffers: memBuffers,
      available: memAvailable,
      usagePercent: ((memUsed / memTotal) * 100).toFixed(2),
    };
  } catch (e) {
    return null;
  }
}

function parseDiskInfo() {
  try {
    const output = execSync("df -B1 --output=source,fstype,size,used,avail,pcent,target")
      .toString();
    const lines = output.split("\n").slice(1);
    return lines
      .filter((line) => line.trim())
      .map((line) => {
        const parts = line.split(/\s+/);
        return {
          filesystem: parts[0],
          tip: parts[1],
          velicina: parseInt(parts[2]),
          koristi: parseInt(parts[3]),
          dostupno: parseInt(parts[4]),
          procenat: parts[5],
          montirano: parts[6],
        };
      });
  } catch (e) {
    return [];
  }
}

function parseCpuInfo() {
  try {
    const loadAvg = require("os").loadavg();
    const cpus = require("os").cpus();
    const cpuCount = cpus.length;
    let totalIdle = 0;
    let totalTick = 0;

    cpus.forEach((cpu) => {
      for (const type in cpu.times) {
        totalTick += cpu.times[type];
      }
      totalIdle += cpu.times.idle;
    });

    const usage = ((1 - totalIdle / totalTick) * 100).toFixed(2);

    return {
      brojCPU: cpuCount,
      loadAverage: loadAvg,
      usagePercent: usage,
      model: cpus[0].model,
      speed: cpus[0].speed,
    };
  } catch (e) {
    return null;
  }
}

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  try {
    if (name === "proveri_sistem") {
      const disk = execSync("df -h /").toString();
      const mem = parseMemoryInfo();
      const cpu = parseCpuInfo();
      const uptime = execSync("uptime -p").toString().trim();

      return {
        content: [
          {
            type: "text",
            text: `## Sistemske Informacije

### CPU
- Model: ${cpu?.model || "N/A"}
- Broj jezgara: ${cpu?.brojCPU || "N/A"}
- Load Average: ${cpu?.loadAverage?.join(", ") || "N/A"}
- Usage: ${cpu?.usagePercent || "N/A"}%

### Memorija
- Total: ${mem ? (mem.total / 1024 / 1024 / 1024).toFixed(2) + " GB" : "N/A"}
- Used: ${mem ? (mem.used / 1024 / 1024 / 1024).toFixed(2) + " GB" : "N/A"}
- Free: ${mem ? (mem.free / 1024 / 1024 / 1024).toFixed(2) + " GB" : "N/A"}
- Usage: ${mem ? mem.usagePercent + "%" : "N/A"}

### Disk
\`\`\`
${disk}\`\`\`

### Uptime
${uptime}`,
          },
        ],
      };
    }

    if (name === "proveri_cpu") {
      const cpu = parseCpuInfo();
      const top = args.top || 10;
      const topProcesses = execSync(`ps aux --sort=-%cpu | head -${top + 1}`)
        .toString();

      return {
        content: [
          {
            type: "text",
            text: `## CPU Informacije

### Statistika
- Model: ${cpu?.model || "N/A"}
- Broj jezgara: ${cpu?.brojCPU || "N/A"}
- Load Average (1, 5, 15 min): ${cpu?.loadAverage?.join(", ") || "N/A"}
- Trenutna upotreba: ${cpu?.usagePercent || "N/A"}%

### Top ${top} Procesa po CPU
\`\`\`${topProcesses}\`\`\``,
          },
        ],
      };
    }

    if (name === "proveri_mrezu") {
      const detailed = args.detailed || false;
      let networkInfo;

      if (detailed) {
        const interfaces = execSync("ip -s link").toString();
        const connections = execSync("ss -tuln").toString();
        networkInfo = `### Mrežne Interfejse
\`\`\`${interfaces}\`\`\`

### Aktivni Portovi
\`\`\`${connections}\`\`\``;
      } else {
        const stats = execSync("cat /proc/net/dev").toString();
        networkInfo = `### Mrežne Statistike
\`\`\`${stats}\`\`\``;
      }

      return {
        content: [
          {
            type: "text",
            text: `## Mrežne Informacije

${networkInfo}`,
          },
        ],
      };
    }

    if (name === "proveri_disk") {
      const disks = parseDiskInfo();
      let diskOutput = "```\n";
      diskOutput +=
        "Filesystem      Type      Size      Used      Avail    Use%    Mounted\n";
      diskOutput += "-".repeat(85) + "\n";

      disks.forEach((d) => {
        diskOutput += `${d.filesystem.padEnd(15)} ${d.tip.padEnd(8)} ${(d.velicina / 1024 / 1024 / 1024).toFixed(2).padStart(8)} GB ${(d.koristi / 1024 / 1024 / 1024).toFixed(2).padStart(8)} GB ${(d.dostupno / 1024 / 1024 / 1024).toFixed(2).padStart(8)} GB ${d.procenat.padStart(4)}   ${d.montirano}\n`;
      });
      diskOutput += "```";

      return {
        content: [
          {
            type: "text",
            text: `## Disk Informacije

${diskOutput}`,
          },
        ],
      };
    }

    if (name === "proveri_procese") {
      const limit = args.limit || 20;
      const sortBy = args.sortBy || "cpu";
      const sortFlag = sortBy === "cpu" ? "-%cpu" : "-%mem";
      const processes = execSync(`ps aux --sort=${sortFlag} | head -${limit + 1}`)
        .toString();

      return {
        content: [
          {
            type: "text",
            text: `## Aktivni Procesi (sortirani po ${sortBy.toUpperCase()})

Top ${limit} procesa:
\`\`\`${processes}\`\`\``,
          },
        ],
      };
    }

    throw new Error(`Nepoznat alat: ${name}`);
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Greška pri izvršavanju alata "${name}": ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: RESOURCES,
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  try {
    if (uri === "system://cpu") {
      const cpu = parseCpuInfo();
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(cpu, null, 2),
          },
        ],
      };
    }

    if (uri === "system://memory") {
      const mem = parseMemoryInfo();
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(mem, null, 2),
          },
        ],
      };
    }

    if (uri === "system://disk") {
      const disks = parseDiskInfo();
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(disks, null, 2),
          },
        ],
      };
    }

    if (uri === "system://network") {
      const { stdout } = await runCommand("cat /proc/net/dev");
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify({ raw: stdout }, null, 2),
          },
        ],
      };
    }

    if (uri === "system://uptime") {
      const { stdout } = await runCommand("uptime");
      return {
        contents: [
          {
            uri,
            mimeType: "text/plain",
            text: stdout,
          },
        ],
      };
    }

    if (uri === "system://hostname") {
      const { stdout } = await runCommand("hostname");
      return {
        contents: [
          {
            uri,
            mimeType: "text/plain",
            text: stdout,
          },
        ],
      };
    }

    throw new Error(`Nepoznat resource: ${uri}`);
  } catch (error) {
    return {
      contents: [
        {
          uri,
          mimeType: "text/plain",
          text: `Greška: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: PROMPTS,
}));

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  try {
    if (name === "system-analysis") {
      const focus = args.focus || "all";
      return {
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: `Molim te analiziraj kompletan status Ubuntu sistema.

Fokus: ${focus}

Koristi sledece MCP alate:
1. \`proveri_sistem\` - Osnovne sistemske informacije
2. \`proveri_cpu\` - Detaljne CPU informacije
3. \`proveri_disk\` - Informacije o diskovima
4. \`proveri_mrezu\` - Mrezne statistike

Zatim mi daj:
- Kompletan pregled stanja sistema
- Uočene probleme
- Preporuke za poboljšanje performansi`,
            },
          },
        ],
      };
    }

    if (name === "resource-report") {
      const timeframe = args.timeframe || "current";
      return {
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: `Generiši detaljan izveštaj o upotrebi resursa.

Vremenski okvir: ${timeframe}

Koristi sledece alate:
1. \`proveri_sistem\` - Sveobuhvatni pregled
2. \`proveri_procese\` - Lista procesa
3. \`proveri_disk\` - Stanje diskova

Izveštaj treba da sadrži:
- Trenutnu upotrebu CPU, memorije i diska
- Procese koji najviše troše resurse
- Preporuke za optimizaciju`,
            },
          },
        ],
      };
    }

    if (name === "troubleshoot-performance") {
      const symptom = args.symptom;
      if (!symptom) {
        throw new Error("Argument 'symptom' je obavezan");
      }

      const symptomMap = {
        slow: "Sistem je spor",
        "high-cpu": "Visoka upotreba CPU-a",
        "high-memory": "Visoka upotreba memorije",
        "high-disk": "Visoka upotreba diska",
      };

      return {
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: `Rešavanje problema sa performansama.

Simptom: ${symptomMap[symptom] || symptom}

Prvo koristi odgovarajuce alate za dijagnostiku:
- Za CPU: \`proveri_cpu\`
- Za memoriju: \`proveri_sistem\`
- Za disk: \`proveri_disk\`
- Za procese: \`proveri_procese\`

Zatim:
1. Identifikuj uzrok problema
2. Predloži konkretne korake za rešavanje
3. Daj preventivne preporuke`,
            },
          },
        ],
      };
    }

    throw new Error(`Nepoznat prompt: ${name}`);
  } catch (error) {
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Greška pri generisanju prompta: ${error.message}`,
          },
        },
      ],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server pokrenut!");
}

main().catch(console.error);
