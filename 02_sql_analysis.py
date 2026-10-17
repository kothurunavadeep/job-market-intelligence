"""
Step 2 - SQL ANALYSIS
Loads the cleaned data into SQLite, runs every tagged query in
02_analysis_queries.sql and exports each result to outputs/sql_results/<id>_<name>.csv
"""
import os
import re
import sqlite3
import pandas as pd

DB = "outputs/job_market.db"
os.makedirs("outputs/sql_results", exist_ok=True)
if os.path.exists(DB):
    os.remove(DB)

con = sqlite3.connect(DB)
jobs = pd.read_csv("data/clean_jobs.csv")
skills = pd.read_csv("data/job_skills.csv")

# booleans -> 0/1 for SQL friendliness
for c in ["salary_disclosed", "is_unpaid", "is_data_role", "is_tech_role", "is_future_start"]:
    jobs[c] = jobs[c].astype(int)

jobs.to_sql("jobs", con, index=False)
skills.to_sql("job_skills", con, index=False)
con.execute("CREATE INDEX idx_jobs_id ON jobs(job_id)")
con.execute("CREATE INDEX idx_skills_job ON job_skills(job_id)")
con.execute("CREATE INDEX idx_skills_skill ON job_skills(skill)")
con.commit()

sql = open("02_analysis_queries.sql").read()

# split into statements, track [Qnn] tags
statements = [s.strip() for s in sql.split(";") if s.strip()]
results = {}
for stmt in statements:
    tag = re.search(r"--\s*\[(Q\d+)\]\s*(\w+)", stmt)
    # strip comment-only lines for execution check
    body = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
    if not body:
        continue
    if tag:
        qid, name = tag.groups()
        df = pd.read_sql_query(body, con)
        fn = f"outputs/sql_results/{qid}_{name}.csv"
        df.to_csv(fn, index=False)
        results[qid] = (name, df)
        print(f"{qid} {name}: {len(df)} rows")
    else:
        con.execute(body)
con.commit()
con.close()

# quick console peek at headline queries
for q in ["Q01", "Q05", "Q13", "Q10"]:
    name, df = results[q]
    print(f"\n=== {q} {name} ===")
    print(df.head(12).to_string(index=False))
