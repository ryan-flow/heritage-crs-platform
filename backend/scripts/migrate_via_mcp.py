"""Migrate SQLite → Supabase PostgreSQL via MCP execute_sql.

Handles type conversions: BOOLEAN, TIMESTAMP, TEXT, etc.
"""
import json, sqlite3, os, subprocess, sys, time

TMP = "D:/桌面/毕业设计/backend/temp_migrate"
DB = "d:/桌面/毕业设计/backend/heritage_platform.db"
TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
PROJECT = "pvbfnscxejyommijiico"


def get_session():
    result = subprocess.run([
        "curl", "-s", "-D", "-", "-X", "POST",
        f"https://mcp.supabase.com/mcp?project_ref={PROJECT}",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json, text/event-stream",
        "-d", json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                          "params": {"protocolVersion": "2025-11-25", "capabilities": {},
                                     "clientInfo": {"name": "claude", "version": "1.0"}}})
    ], capture_output=True, text=True)
    for line in result.stderr.split("\n"):
        if "mcp-session-id:" in line.lower():
            return line.split(":", 1)[1].strip()
    for line in result.stdout.split("\n"):
        if "mcp-session-id:" in line.lower():
            return line.split(":", 1)[1].strip()
    return ""


def mcp_call(sid, name, args):
    """Call an MCP tool and return response text."""
    payload = json.dumps({"jsonrpc": "2.0", "id": 900, "method": "tools/call",
                          "params": {"name": name, "arguments": args}})
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"https://mcp.supabase.com/mcp?project_ref={PROJECT}",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json, text/event-stream",
        "-H", f"Mcp-Session-Id: {sid}", "-d", payload
    ], capture_output=True, text=True)
    resp = json.loads(result.stdout)
    return resp["result"]["content"][0]["text"]


def format_value(v, pg_type):
    """Format a value for PostgreSQL INSERT."""
    if v is None:
        return "NULL"
    if pg_type in ("BOOLEAN",):
        return "true" if v else "false"
    if pg_type in ("INTEGER", "SERIAL"):
        return str(int(v))
    if pg_type in ("DOUBLE PRECISION", "FLOAT", "NUMERIC"):
        return str(float(v))
    # TEXT / VARCHAR / TIMESTAMP
    s = str(v)
    s = s.replace("'", "''")  # escape single quotes
    return f"'{s}'"


def get_pg_types(table, cols, c):
    """Guess PostgreSQL column types from SQLite schema."""
    c.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
    sql = (c.fetchone() or [""])[0] or ""
    types = {}
    for col in cols:
        if f"\"{col}\"" in sql:
            idx = sql.index(f"\"{col}\"") + len(col) + 2
        elif f"`{col}`" in sql:
            idx = sql.index(f"`{col}`") + len(col) + 2
        else:
            idx = sql.index(f" {col} ") + len(col) + 1 if f" {col} " in sql else -1
        if idx > 0:
            rest = sql[idx:].strip().split(",")[0].split("\n")[0].strip()
            if rest.startswith("INTEGER"):
                types[col] = "INTEGER"
            elif rest.startswith("BOOLEAN"):
                types[col] = "BOOLEAN"
            elif rest.startswith("FLOAT") or rest.startswith("DOUBLE"):
                types[col] = "DOUBLE PRECISION"
            elif rest.startswith("NUMERIC"):
                types[col] = "NUMERIC"
            elif rest.startswith("TIMESTAMP") or rest.startswith("DATETIME"):
                types[col] = "TIMESTAMP"
            else:
                types[col] = "TEXT"
        else:
            types[col] = "TEXT"
    return types


def main():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence') AND name NOT LIKE 'pg%' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]

    sid = get_session()
    if not sid:
        print("ERROR: Could not get MCP session")
        return

    total_inserts = 0
    for table in tables:
        c.execute(f'SELECT * FROM "{table}"')
        rows = c.fetchall()
        if not rows:
            continue
        cols = [d[0] for d in c.description]
        pg_types = get_pg_types(table, cols, c)

        inserts = []
        for row in rows:
            vals = [format_value(row[j], pg_types.get(cols[j], "TEXT")) for j in range(len(cols))]
            qcols = ", ".join(f'"{col}"' for col in cols)
            sql = f'INSERT INTO "{table}" ({qcols}) VALUES ({", ".join(vals)});'
            inserts.append(sql)

        # Batch insert
        batch_size = 200
        for i in range(0, len(inserts), batch_size):
            batch = inserts[i:i + batch_size]
            batch_sql = "BEGIN; " + " ".join(batch) + " COMMIT;"
            result = mcp_call(sid, "execute_sql", {"query": batch_sql})
            if "error" in result.lower():
                # Try without transaction wrapper
                for sql in batch:
                    r2 = mcp_call(sid, "execute_sql", {"query": sql})
                    if "error" in r2.lower():
                        print(f"  FAIL {table}: {sql[:60]}... → {r2[:80]}")
                    else:
                        total_inserts += 1
            else:
                total_inserts += len(batch)
            if i % 500 == 0:
                print(f"  {table}: {min(i+batch_size, len(inserts))}/{len(inserts)}")

        print(f"  {table}: {len(inserts)} rows ✅")
        time.sleep(0.5)

    print(f"\nTotal: {total_inserts} rows migrated")
    conn.close()


if __name__ == "__main__":
    main()
