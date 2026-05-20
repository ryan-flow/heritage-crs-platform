"""Generate INSERT batches with proper PostgreSQL type handling."""
import json, sqlite3, os

TMP = "D:/桌面/毕业设计/backend/temp_migrate"
DB = "d:/桌面/毕业设计/backend/heritage_platform.db"

os.makedirs(TMP, exist_ok=True)
for f in os.listdir(TMP):
    if f.endswith(".json"):
        os.unlink(os.path.join(TMP, f))

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Get boolean columns per table
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
table_cols = {}
for row in cur.fetchall():
    tname = row[0]
    sql = row[1]
    bool_cols = set()
    for line in sql.split(","):
        line = line.strip().strip(")")
        parts = line.split()
        if len(parts) >= 2 and parts[1].upper() == "BOOLEAN":
            bool_cols.add(parts[0].strip('"').strip("`"))
    table_cols[tname] = bool_cols

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence') AND name NOT LIKE 'pg%' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]

total = 0
batch_num = 0
for table in tables:
    if table == "personas":
        continue
    cur.execute(f'SELECT * FROM "{table}"')
    rows = cur.fetchall()
    if not rows:
        continue
    cols = [d[0] for d in cur.description]
    bools = table_cols.get(table, set())

    # Batch by 100 rows
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        sql_parts = []
        for row in batch:
            vals = []
            for j, v in enumerate(row):
                col = cols[j]
                if v is None:
                    vals.append("NULL")
                elif col in bools:
                    vals.append("true" if v else "false")
                elif isinstance(v, str):
                    vals.append(f"'{v.replace(chr(39), chr(39)+chr(39))}'")
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                elif isinstance(v, bool):
                    vals.append("true" if v else "false")
                else:
                    vals.append(f"'{str(v)}'")
            qcols = ", ".join(f'"{c}"' for c in cols)
            sql_parts.append(f'INSERT INTO "{table}" ({qcols}) VALUES ({", ".join(vals)})')
        sql = ";\n".join(sql_parts) + ";\n"

        payload = json.dumps({
            "jsonrpc": "2.0", "id": 1000 + batch_num,
            "method": "tools/call",
            "params": {"name": "execute_sql", "arguments": {"query": sql}},
        })
        fname = os.path.join(TMP, f"batch_{batch_num:04d}.json")
        with open(fname, "w") as f:
            f.write(payload)
        batch_num += 1
        total += len(batch)

    print(f"{table}: {len(rows)} rows")

print(f"BATCHES={batch_num}")
conn.close()
