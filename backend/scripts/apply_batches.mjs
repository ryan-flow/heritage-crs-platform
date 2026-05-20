import fs from "fs";
import path from "path";
import https from "https";

const TOKEN = process.env.SUPABASE_ACCESS_TOKEN || "";
const REF = "pvbfnscxejyommijiico";
const TMP = "D:/桌面/毕业设计/backend/temp_migrate";

function httpsPost(body, extraHeaders = {}) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = https.request(
      {
        hostname: "mcp.supabase.com",
        path: `/mcp?project_ref=${REF}`,
        method: "POST",
        headers: {
          Authorization: `Bearer ${TOKEN}`,
          "Content-Type": "application/json",
          Accept: "application/json, text/event-stream",
          "Content-Length": Buffer.byteLength(data),
          ...extraHeaders,
        },
      },
      (res) => {
        let body = "";
        res.on("data", (chunk) => (body += chunk));
        res.on("end", () => {
          try {
            resolve({ headers: res.headers, body: JSON.parse(body) });
          } catch {
            resolve({ headers: res.headers, body });
          }
        });
      }
    );
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

async function main() {
  // Initialize session
  const init = await httpsPost({
    jsonrpc: "2.0", id: 0, method: "initialize",
    params: { protocolVersion: "2025-11-25", capabilities: {}, clientInfo: { name: "claude", version: "1.0" } },
  });
  const sid = init.headers["mcp-session-id"];
  if (!sid) { console.error("No session ID"); process.exit(1); }
  console.log(`Session: ${sid.slice(0, 30)}...`);

  // Get batch files
  const files = fs.readdirSync(TMP).filter((f) => f.startsWith("batch_") && f.endsWith(".json")).sort();
  console.log(`Files: ${files.length}`);

  let ok = 0, fail = 0;
  for (const file of files) {
    const payload = JSON.parse(fs.readFileSync(path.join(TMP, file), "utf8"));

    const resp = await httpsPost(
      {
        jsonrpc: "2.0", id: payload.id, method: "tools/call",
        params: { name: "execute_sql", arguments: { query: payload.params.arguments.query } },
      },
      { "Mcp-Session-Id": sid }
    );

    const result = resp.body?.result?.content?.[0]?.text || JSON.stringify(resp.body);
    const isErr = resp.body?.result?.isError || result.includes('"error"');
    if (isErr) {
      fail++;
      console.log(`❌ ${file}: ${result.slice(0, 100)}`);
    } else {
      ok++;
    }

    if ((ok + fail) % 10 === 0) console.log(`  ${ok + fail}/${files.length}`);
    await new Promise((r) => setTimeout(r, 200));
  }

  console.log(`\n✅ ${ok} OK, ❌ ${fail} failed (${files.length} total)`);
}

main().catch(console.error);
