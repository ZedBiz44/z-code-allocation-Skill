#!/usr/bin/env node



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
  const allowed = {
    allocate: ["request-id", "name-key", "folder", "lane", "page-type", "topic-name", "create-lane", "create-topic"],
    confirm: ["z-code", "notion-url", "record-title"], failed: ["z-code", "reason"],
    status: ["request-id"], lookup: ["name-key", "folder"], resolve: ["z-code"], catalogue: [],
    "rename-record": ["z-code", "notion-url", "record-title", "reason"],
    "delete-record": ["z-code", "notion-url", "reason"],
    "rename-lane": ["folder", "name-key", "new-name-key", "reason"],
  };
  if (!(command in allowed)) throw new Error(`Unknown command: ${command}`);
  const values = {};
  for (let index = 1; index < argv.length; index += 1) {
    const flag = argv[index];
    if (!flag?.startsWith("--")) throw new Error(`Invalid argument: ${flag || "<missing>"}`);
    const name = flag.slice(2);
    if (!allowed[command].includes(name) || name in values) throw new Error(`Unknown or duplicate flag: ${flag}`);
    if (name === "create-lane" || name === "create-topic") {
      values[name] = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value?.trim() || value.startsWith("--")) throw new Error(`Missing value: ${flag}`);
    values[name] = value;
    index += 1;
  }
  return { command, values };
}

function requireValues(values, names) {
  const missing = names.filter((name) => !values[name]);
  if (missing.length) throw new Error(`Missing required arguments: ${missing.map((name) => `--${name}`).join(", ")}`);
}

async function apiRequest(method, endpoint, key, body, options = {}) {
  if (new URL(endpoint).pathname.includes("/v1/admin/")) {
    key = process.env.ZCODE_ADMIN_API_KEY || key;
  }
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
      try { result = JSON.parse(text); } catch { throw new Error("Invalid JSON response; retain request ID and check status"); }
      if (!result || Array.isArray(result) || typeof result !== "object") throw new Error("Invalid response object");
      if (!response.ok) {
        if (
          options.notFoundResult !== undefined
          && response.status === 404
          && result?.detail?.code === "not_found"
        ) {
          return options.notFoundResult;
        }
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
    requireValues(values, ["request-id", "name-key", "folder", "page-type"]);
    if ((values["create-lane"] || values["create-topic"]) && !values["topic-name"]) {
      throw new Error("--topic-name is required with --create-lane or --create-topic");
    }
    if (values["topic-name"] && values.lane) {
      throw new Error("Use --name-key to select a named lane; omit --lane when using --topic-name");
    }
    result = await apiRequest("POST", `${url}/v1/allocate`, key, {
      request_id: values["request-id"],
      name_key: values["name-key"],
      folder_key: values.folder,
      ...(values.lane ? { knowledge_lane: values.lane } : {}),
      ...(values["topic-name"] ? { topic_name: values["topic-name"] } : {}),
      ...(values["create-lane"] ? { create_lane: true } : {}),
      ...(values["create-topic"] ? { create_topic: true } : {}),
      page_type: values["page-type"],
      requested_by: agent,
    });
  } else if (command === "confirm") {
    requireValues(values, ["z-code", "notion-url", "record-title"]);
    result = await apiRequest("POST", `${url}/v1/confirm`, key, {
      z_code: values["z-code"], status: "active", notion_url: values["notion-url"],
      record_title: values["record-title"] || null,
    });
  } else if (command === "rename-lane") {
    requireValues(values, ["folder", "name-key", "new-name-key", "reason"]);
    result = await apiRequest("POST", `${url}/v1/admin/rename-lane`, key, {
      folder_key: values.folder, name_key: values["name-key"], new_name_key: values["new-name-key"], reason: values.reason,
    });
  } else if (command === "rename-record" || command === "delete-record") {
    requireValues(values, ["z-code", "notion-url", "reason", ...(command === "rename-record" ? ["record-title"] : [])]);
    result = await apiRequest("POST", `${url}/v1/admin/${command}`, key, {
      z_code: values["z-code"], notion_url: values["notion-url"], reason: values.reason,
      ...(command === "rename-record" ? { record_title: values["record-title"] } : {}),
    });
  } else if (command === "failed") {
    requireValues(values, ["z-code", "reason"]);
    result = await apiRequest("POST", `${url}/v1/confirm`, key, {
      z_code: values["z-code"], status: "failed", reason: values.reason,
    });
  } else if (command === "catalogue") {
    result = await apiRequest("GET", `${url}/v1/catalogue`, key);
  } else if (command === "resolve") {
    requireValues(values, ["z-code"]);
    result = await apiRequest("GET", `${url}/v1/resolve?${new URLSearchParams({ z_code: values["z-code"] })}`, key);
  } else if (command === "status") {
    requireValues(values, ["request-id"]);
    result = await apiRequest("GET", `${url}/v1/status/${encodeURIComponent(values["request-id"])}`, key);
  } else if (command === "lookup") {
    requireValues(values, ["name-key"]);
    const lookupPath = values.folder ? "/v1/lanes/lookup" : "/v1/lookup";
    const query = new URLSearchParams({ name_key: values["name-key"] });
    if (values.folder) query.set("folder_key", values.folder);
    result = await apiRequest(
      "GET",
      `${url}${lookupPath}?${query}`,
      key,
      undefined,
      { notFoundResult: { found: false, name_key: values["name-key"] } },
    );
  } else {
    throw new Error(`Unknown command: ${command}`);
  }
  const required = { "rename-lane": ["lane_id", "name_key"], "rename-record": ["z_code", "record_title", "status"], "delete-record": ["z_code", "status", "mirror_event_id"], allocate: ["z_code", "request_id", "status", "mapping_version"], confirm: ["z_code", "status"], failed: ["z_code", "status"], status: ["request_id", "status"], resolve: ["z_code"], catalogue: ["version", "folders"], lookup: result.found === false ? ["found", "name_key"] : ["name_key", values.folder ? "topics" : "records"] }[command];
  if (required.some(k => result[k] === undefined || result[k] === null)) throw new Error("Incomplete success response; retain request details and reconcile");
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
