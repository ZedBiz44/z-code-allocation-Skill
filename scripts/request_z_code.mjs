#!/usr/bin/env node

import { randomUUID } from "node:crypto";

function configuration() {
  const url = (process.env.ZCODE_ALLOCATOR_URL || "").replace(/\/$/, "");
  const key = process.env.ZCODE_API_KEY || "";
  const agent = (process.env.ZCODE_AGENT_NAME || "").trim().toLowerCase();
  const missing = [
    ["ZCODE_ALLOCATOR_URL", url],
    ["ZCODE_API_KEY", key],
    ["ZCODE_AGENT_NAME", agent],
  ].filter(([, value]) => !value).map(([name]) => name);
  if (missing.length) throw new Error(`Missing required environment values: ${missing.join(", ")}`);
  return { url, key, agent };
}

function parseArgs(argv) {
  const command = argv[0];
  if (!command) throw new Error("A command is required: lookup, allocate, confirm, failed, or status");
  const values = {};
  for (let index = 1; index < argv.length; index += 2) {
    const flag = argv[index];
    if (!flag?.startsWith("--") || argv[index + 1] === undefined) throw new Error(`Invalid argument: ${flag || "<missing>"}`);
    values[flag.slice(2)] = argv[index + 1];
  }
  return { command, values };
}

function requireValues(values, names) {
  const missing = names.filter((name) => !values[name]);
  if (missing.length) throw new Error(`Missing required arguments: ${missing.map((name) => `--${name}`).join(", ")}`);
}

async function apiRequest(method, endpoint, key, body) {
  let lastError;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetch(endpoint, {
        method,
        headers: {
          Authorization: `Bearer ${key}`,
          Accept: "application/json",
          ...(body ? { "Content-Type": "application/json" } : {}),
        },
        ...(body ? { body: JSON.stringify(body) } : {}),
        signal: AbortSignal.timeout(15000),
      });
      const text = await response.text();
      let result;
      try { result = JSON.parse(text); } catch { result = { error: text }; }
      if (!response.ok) {
        console.error(JSON.stringify({ http_status: response.status, ...result }, null, 2));
        process.exit(2);
      }
      return result;
    } catch (error) {
      lastError = error;
      if (attempt === 0) await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
  throw new Error(`Z-Code allocator unavailable: ${lastError?.message || lastError}`);
}

async function main() {
  const { url, key, agent } = configuration();
  const { command, values } = parseArgs(process.argv.slice(2));
  let result;
  if (command === "allocate") {
    requireValues(values, ["name-key", "core", "lane", "page-type"]);
    result = await apiRequest("POST", `${url}/v1/allocate`, key, {
      request_id: values["request-id"] || `${agent}-${randomUUID()}`,
      name_key: values["name-key"],
      z_knowledge_core: values.core.toUpperCase(),
      knowledge_lane: values.lane,
      page_type: values["page-type"],
      requested_by: agent,
    });
  } else if (command === "confirm") {
    requireValues(values, ["z-code", "notion-url"]);
    result = await apiRequest("POST", `${url}/v1/confirm`, key, {
      z_code: values["z-code"], status: "active", notion_url: values["notion-url"],
    });
  } else if (command === "failed") {
    requireValues(values, ["z-code", "reason"]);
    result = await apiRequest("POST", `${url}/v1/confirm`, key, {
      z_code: values["z-code"], status: "failed", reason: values.reason,
    });
  } else if (command === "status") {
    requireValues(values, ["request-id"]);
    result = await apiRequest("GET", `${url}/v1/status/${encodeURIComponent(values["request-id"])}`, key);
  } else if (command === "lookup") {
    requireValues(values, ["name-key"]);
    result = await apiRequest("GET", `${url}/v1/lookup?${new URLSearchParams({ name_key: values["name-key"] })}`, key);
  } else {
    throw new Error(`Unknown command: ${command}`);
  }
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
