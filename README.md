# 🏆 Job Market Intelligence – India 2025
**Python + SQL + Power BI** | 97,929 raw → 93,900 clean job postings | Source: Kaggle *Indian Job Market Dataset 2025* (Naukri)

Cleaned and standardized a 97K-record Indian job market dataset, then extracted and ranked in-demand skills, roles,
locations and salary ranges to show hiring trends for data and tech careers, and designed a Power BI model with DAX
measures and slicers for skill-demand, salary and location insights.

---
## 📦 What is in this package
```
job_market_project/
├── README.md                          ← this file
├── 01_clean_data.py                   ← Python cleaning & standardisation
├── 02_analysis_queries.sql            ← 20 tagged SQL queries (SQLite / ANSI-friendly)
├── 02_sql_analysis.py                 ← loads SQLite, runs queries, exports CSVs
├── 03_powerbi_model.py                ← builds the Power BI star schema
├── 04_visuals_and_excel.py            ← charts, dashboard preview, Excel workbook
├── data/
│   ├── clean_jobs.csv                 ← cleaned fact table (93,900 rows)
│   ├── job_skills.csv                 ← job↔skill pairs (688K rows)
│   └── cleaning_log.json              ← every cleaning step with counts
├── outputs/
│   ├── Job_Market_Insights.xlsx       ← all SQL results + charts + data dictionary
│   ├── job_market.db                  ← SQLite database (open in DB Browser for SQLite)
│   ├── sql_results/                   ← one CSV per query (Q01…Q20)
│   ├── charts/                        ← PNG charts + 00_dashboard_preview.png
│   └── powerbi/
│       ├── data/                      ← 9 star-schema CSVs (import into Power BI)
│       ├── DAX_measures.dax           ← 40+ measures
│       ├── PowerQuery_M.txt           ← typed loaders
│       ├── theme.json                 ← dashboard theme
│       └── Power_BI_Build_Guide.md    ← model, relationships, 4 report pages
```
Run order: `python 01_clean_data.py → 02_sql_analysis.py → 03_powerbi_model.py → 04_visuals_and_excel.py`
(needs `pandas`, `openpyxl`, `matplotlib`; the raw file must be exported to `data/raw_jobs.csv`).

---
## 🧹 Data cleaning (Python)
| Step | Result |
|---|---|
| Exact duplicate rows | 247 removed |
| Duplicate `jobId` | 3 removed |
| Re-posted ads (same company + title + location + description) | 3,779 removed |
| **Total removed** | **4,029 (4.1%)** → 93,900 rows |
| Job titles normalised (brackets, "urgent/hiring/walk-in", seniority words stripped) | 54,996 → 32,030 distinct titles |
| Titles mapped to **26 role families** (rules on title + skills) | 4,002 data-role postings (Analyst 1,302 / Engineer 1,430 / Scientist 1,270) |
| Locations parsed (10,063 raw strings → primary city, tier, work mode) | Bangalore→Bengaluru, Gurgaon/Noida→Delhi NCR, Thane/Navi Mumbai→Mumbai; 1,259 cities, top 40 kept in reports |
| Salary: parsed min/max INR, midpoint & LPA, bands | "Not disclosed" → null; 603 implausible values (<₹1.2L or >₹1.5Cr) nullified; 129 USD rows × 83 |
| Experience parsed → 5 levels | 0.6% missing |
| Posting date | From `jobId` prefix (DDMMYY) for 91,646 rows; validated against "N days ago" (snapshot = 3-Oct-2025) |
| Skills: 719K tags → normalised (e.g. *MS Excel / Advanced Excel → Excel*, *PowerBI → Power BI*) | 31K generic tags dropped ("Data", "Management"…) → 688K clean job–skill pairs |

## 🔍 Key findings
**Skills for data roles (4,002 postings)**
- **Python (40%)** and **SQL (26%)** are the two most requested skills; Machine Learning (19%), Data Analysis (12%), PySpark (11%) follow.
- **Data Analyst postings** ask for: SQL → Data Analysis → **Power BI** → Excel → Python → BI → Tableau.
- **SQL pairs most often with** Python (530 jobs), ETL, Power BI, PySpark and Snowflake.
- **Highest salary premium** (vs. avg data-role pay of ~₹15.7 LPA): Data Architecture (+109%), LangChain and LLM (~+80%), Generative AI (+63%), TensorFlow/PyTorch (+51–59%). Each has only 15–60 salary-disclosed postings, so treat as directional.

**Roles & salary (only salary-disclosed postings; ~34% of the data)**
- Median salary (LPA): **Data Engineer 20.0 · Data Scientist 17.0** · Full Stack 16.5 · Software Eng 14.0 · **Data Analyst 6.0** · Customer Support 3.0.
- Analyst pay climbs steeply with experience: ~₹4 LPA (1–3 yrs) → ~₹11 LPA (3–6) → ~₹19 LPA (6–10).
- **46%** of data postings target 3–6 years of experience; only **3%** are fresher roles.

**Locations**
- Bengaluru leads (19.7% of all jobs; 999 data jobs), then Hyderabad, Delhi NCR, Mumbai, Pune. **Tier-1 cities hold 76%** of postings.
- Bengaluru (₹17.0 LPA avg) and Pune/Hyderabad (~₹16 LPA) pay the most for tech roles; Mumbai (₹9.8 LPA) pays far less despite its size.
- Data roles are more flexible than other jobs: **23% hybrid/remote** vs 4% for non-tech roles.

## ⚠️ Limitations (say these in interviews – they show maturity)
1. **Snapshot, not a time series.** Dataset = active postings on ~3 Oct 2025; 92% are from Sep–Oct, so no trend analysis over months.
2. **Salary bias.** Only ~34% disclose salary, skewed to tech/mid-level; data-analyst salary sample = 308 postings.
3. **Role families are rule-based**; some edge titles may be misclassified (≈11% fall in "Other").
4. **Recruiter-agency postings** (e.g. Purview, Krazy Mantra) inflate "top employer" counts.
5. USD→INR uses a flat rate of 83 (129 rows).

## 📝 Resume bullets (ready to paste)
- Cleaned and standardized a **97K-record** Indian job-market dataset (Kaggle/Naukri) using **Python (pandas)** and **SQL**: removed 4K duplicate/reposted ads, collapsed **55K raw job titles into 32K standardized titles / 26 role families**, parsed 10K location strings into cities, tiers and work modes, and normalised salary and experience fields.
- Built a SQL analysis layer (**window functions, CTEs, self-joins**) ranking in-demand skills, roles, locations and salary ranges; found **Python (40%) and SQL (26%)** are the most requested skills in data roles, with GenAI/LLM skills commanding **~60–80% salary premiums** (directional; small samples).
- Designed a **Power BI** star-schema model (9 tables) with **40+ DAX measures** and slicers for skill demand, salary and location insights across 4 report pages.

## 🎤 Interview talking points
- *Why median, not mean, for salary?* Heavy right-skew (a few ₹1Cr+ postings); median is robust.
- *How did you handle undisclosed salary?* Kept rows for volume metrics, nulled salary, added a `Salary Reliability` measure for thin samples.
- *Why a bridge table for skills?* Many-to-many between jobs and skills; avoids exploding the fact table and lets slicers filter via bidirectional relationship.
- *How did you validate the posting date?* jobId prefix + "N days ago" implied the same snapshot date (3-Oct-2025) for 75% of rows.
