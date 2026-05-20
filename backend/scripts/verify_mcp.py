"""Verify Supabase data migration by checking row counts via MCP API."""
import json, os, subprocess, sys

SID = os.environ.get("SID", "")
TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
PROJECT = "pvbfnscxejyommijiico"


def mcp_call(name, args, sid):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 400, "method": "tools/call",
        "params": {"name": name, "arguments": args}
    })
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://mcp.supabase.com/mcp?project_ref={PROJECT}",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json, text/event-stream",
        "-H", f"Mcp-Session-Id: {SID}",
        "-d", payload
    ], capture_output=True, text=True)
    resp = json.loads(result.stdout)
    txt = resp["result"]["content"][0]["text"]
    start = txt.find("[")
    if start >= 0:
        end = txt.rfind("]") + 1
        return json.loads(txt[start:end])
    return txt


# Check row counts
rows = mcp_call("execute_sql", {"query": "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname;"}, SID)
total = 0
for r in rows:
    print(f"  {r['relname']:30s} {r['n_live_tup']:>5d}")
    total += r["n_live_tup"]
print(f"  {'-'*36}")
print(f"  {'TOTAL':30s} {total:>5d}")
