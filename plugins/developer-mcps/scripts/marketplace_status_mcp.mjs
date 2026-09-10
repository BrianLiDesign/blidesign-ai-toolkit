#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const pluginRoot = resolve(scriptDirectory, "..");

function readJson(relativePath) {
  return JSON.parse(readFileSync(join(pluginRoot, relativePath), "utf8"));
}

function marketplaceStatus() {
  const catalog = readJson("assets/catalog.json");
  const manifestExists = existsSync(join(pluginRoot, ".codex-plugin", "plugin.json"));
  const skillExists = existsSync(
    join(pluginRoot, "skills", "portable-mcp-status", "SKILL.md"),
  );

  return {
    healthy: manifestExists && skillExists,
    marketplace: catalog.marketplace,
    pluginCount: catalog.plugins.length,
    plugins: catalog.plugins,
    profileCount: catalog.profiles.length,
    profiles: catalog.profiles,
    vendoredSkillCount: catalog.vendoredSkillCount,
    upstreamSources: catalog.upstreamSources,
  };
}

function response(id, result) {
  process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", id, result })}\n`);
}

function errorResponse(id, error, code = -32603) {
  process.stdout.write(
    `${JSON.stringify({
      jsonrpc: "2.0",
      id,
      error: { code, message: error instanceof Error ? error.message : String(error) },
    })}\n`,
  );
}

const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
lines.on("line", (line) => {
  if (!line.trim()) return;
  let request;
  try {
    request = JSON.parse(line);
    if (request.id === undefined) return;

    if (request.method === "initialize") {
      response(request.id, {
        protocolVersion: request.params?.protocolVersion ?? "2025-06-18",
        capabilities: { tools: {} },
        serverInfo: { name: "portable-marketplace-status", version: "0.1.0" },
      });
      return;
    }

    if (request.method === "tools/list") {
      response(request.id, {
        tools: [
          {
            name: "marketplace_status",
            description:
              "Report portable marketplace plugin, profile, provenance, and vendored-skill counts.",
            inputSchema: { type: "object", properties: {}, additionalProperties: false },
          },
        ],
      });
      return;
    }

    if (request.method === "tools/call") {
      if (request.params?.name !== "marketplace_status") {
        throw new Error(`Unknown tool: ${request.params?.name ?? "missing"}`);
      }
      const status = marketplaceStatus();
      response(request.id, {
        content: [{ type: "text", text: JSON.stringify(status, null, 2) }],
        structuredContent: status,
      });
      return;
    }

    errorResponse(request.id, `Method not found: ${request.method}`, -32601);
  } catch (error) {
    errorResponse(request?.id ?? null, error);
  }
});
