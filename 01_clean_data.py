"""
Step 1 - DATA CLEANING & STANDARDIZATION
Indian Job Market Intelligence 2025

Input : data/raw_jobs.csv  (converted from the Kaggle xlsx)
Output: data/clean_jobs.csv, data/job_skills.csv, data/cleaning_log.json
"""
import re
import json
import pandas as pd
import numpy as np

RAW = "data/raw_jobs.csv"
log = {}

df = pd.read_csv(RAW, dtype=str)
log["raw_rows"] = len(df)

# ---------------------------------------------------------------- 1. DUPLICATES
n = len(df)
df = df.drop_duplicates()
log["exact_duplicates_removed"] = n - len(df)

n = len(df)
df = df.drop_duplicates(subset="jobId", keep="first")
log["duplicate_jobid_removed"] = n - len(df)

# same company + title + location + description = reposted ad
n = len(df)
df = df.drop_duplicates(subset=["companyName", "title", "location", "jobDescription"], keep="first")
log["reposted_ads_removed"] = n - len(df)

# ---------------------------------------------------------------- 2. TEXT TIDY
for c in ["title", "companyName", "location", "tagsAndSkills"]:
    df[c] = df[c].fillna("").str.strip().str.replace(r"\s+", " ", regex=True)
df["companyName"] = df["companyName"].replace("", "Unknown")

# ---------------------------------------------------------------- 3. JOB TITLE NORMALIZATION
SENIORITY_WORDS = r"\b(sr|snr|senior|jr|junior|lead|principal|staff|associate|trainee|intern|fresher|head|chief|assistant|asst)\b\.?"


def clean_title(t: str) -> str:
    t = t.lower()
    t = re.sub(r"walk[- ]?in( interview| drive)?|freshers?( only)?\s*[-:]", " ", t)
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)          # drop bracket text
    t = re.sub(r"[-|/,:@].*$", lambda m: " " if m.group(0)[0] in "-|:@" else m.group(0), t)
    t = re.sub(r"\b(opening|hiring|urgent|vacancy|requirement|walk[- ]?in|for|immediate|joiner)\b", " ", t)
    t = re.sub(r"[^a-z0-9+#&. ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


df["title_clean"] = df["title"].map(clean_title)

# Role family mapping (ordered: first match wins)
DATA_SKILL_RX = re.compile(r"\b(sql|power ?bi|tableau|python|excel|looker|qlik|dax|data analy|data visual|statistics|r programming|business intelligence)\b")

ROLE_RULES = [
    ("Data Scientist",        r"data scien|machine learning|\bml\b|\bai\b|genai|gen ai|llm|nlp|deep learning|computer vision|\bai ?/ ?ml"),
    ("Data Engineer",         r"data engineer|\betl\b|big data|databricks|snowflake|data architect|\bdwh\b|data warehouse|hadoop|spark|data ops|dataops|analytics engineer"),
    ("Data Analyst",          r"data analy|bi analy|bi developer|bi engineer|power ?bi|tableau|reporting analy|\bmis\b|insight|analytics|business intelligence|looker|qlik|data visuali|decision sci"),
    ("QA / Testing",          r"\bqa\b|quality analyst|quality assurance|tester|testing|test engineer|automation test|sdet"),
    ("Cyber Security",        r"security analyst|cyber|infosec|\bsoc\b|penetration|security architect|security engineer"),
    ("Finance & Accounting",  r"financ|account(ant|s|ing)|audit|\btax|\bgst\b|banking|loan|credit|treasury|payable|receivable|record to report|procure to pay|order to cash|company secretary|\bcommis\b|chef de partie"),
    ("Full Stack Developer",  r"full ?stack"),
    ("Frontend Developer",    r"front ?end|react|angular|ui developer|vue|web developer|wordpress"),
    ("Backend Developer",     r"back ?end|java developer|python developer|node|\.net|golang|php|django|spring|api developer|java engineer"),
    ("Mobile Developer",      r"android|\bios\b|flutter|mobile app|react native"),
    ("DevOps / Cloud",        r"devops|cloud|\baws\b|azure|\bsre\b|site reliability|kubernetes|infrastructure|system admin|network engineer|dba|database admin"),
    ("Software Engineer",     r"software|developer|programmer|application (developer|lead|support|tech)|\bsde\b|technical lead|tech lead|solution architect|sap |salesforce|servicenow|oracle|mainframe|embedded|firmware|technology"),
    ("Consulting & Architecture", r"consultant|architect"),
    ("Product / Project Mgmt", r"product manager|product owner|project manager|program manager|scrum|delivery manager|project coordinator|\bpmo\b"),
    ("UI/UX & Design",        r"designer|\bux\b|\bui\b|graphic|creative|animator|video editor|illustrator|interior|architect(?:ural)? "),
    ("Customer Support / BPO", r"customer (support|service|care|success|experience)|support executive|process associate|voice|chat support|bpo|trust & safety|call cent|tele ?caller|tele ?sales|helpdesk|service desk|technical support|content moderat|back office|data entry|process (executive|specialist)"),
    ("Sales & Business Dev",  r"sales|business development|\bbde\b|relationship (manager|officer)|account (executive|manager)|inside sales|\bbd\b|business executive|business manager|branch manager|area manager|territory|channel|field executive|insurance advisor|financial advisor"),
    ("Marketing & Content",   r"marketing|\bseo\b|content|social media|copywrit|brand|writer|editor|journalist|public relations|\bpr\b|influencer|community manager"),
    ("HR & Recruitment",      r"\bhr\b|recruit|talent|human resource|payroll|hrbp|people (ops|partner)|\bhrms\b"),
    ("Operations & Logistics", r"operations|logistics|supply chain|warehouse|procurement|purchase|\bstore\b|dispatch|delivery|inventory|fleet|merchandis|planner|sourcing|vendor"),
    ("Healthcare",            r"nurse|doctor|medical|pharma|clinical|physician|hospital|dental|lab technician|patient|therapist|radiolog|surgeon|health"),
    ("Education & Training",  r"teacher|faculty|trainer|professor|tutor|lecturer|counsel|academic|educator|principal"),
    ("Engineering (Non-IT)",  r"mechanical|civil|electrical|site engineer|production|maintenance|quality engineer|\bplant\b|manufactur|electronics|instrumentation|\bcnc\b|welder|technician|supervisor|\bqc\b|\bhse\b|safety|fire"),
    ("Admin & General Mgmt",  r"manager|executive|officer|administrator|receptionist|director|\bhead\b|coordinator|secretary|assistant|supervisor|associate|specialist|team lead|team leader|general"),
]
ROLE_RULES = [(name, re.compile(p)) for name, p in ROLE_RULES]
GENERIC_ANALYST = re.compile(r"analyst")


def role_family(t: str, skills: str = "") -> str:
    t = re.sub(r"\bwalk ?in\b", " ", t)
    for name, rx in ROLE_RULES:
        if rx.search(t):
            return name
    # generic "analyst" / "associate analyst" -> decide by skills
    if GENERIC_ANALYST.search(t):
        return "Data Analyst" if DATA_SKILL_RX.search(skills) else "Business / Research Analyst"
    if re.search(r"engineer", t):
        return "Engineering (Non-IT)"
    # last resort: skills-based
    if re.search(r"\b(python|java|javascript|sql|react|aws)\b", skills):
        return "Software Engineer"
    return "Other"


# "Business Analyst" is a data-adjacent role only when data skills are listed
_skills_lc = df["tagsAndSkills"].str.lower()
def _family(row_t, row_s):
    if re.search(r"business analy", row_t) and not re.search(r"data|bi\b|insight|analytics", row_t):
        return "Data Analyst" if DATA_SKILL_RX.search(row_s) else "Business / Research Analyst"
    return role_family(row_t, row_s)

df["role_family"] = [_family(t, s) for t, s in zip(df["title_clean"], _skills_lc)]

# Canonical title: strip seniority words so "Sr. Data Analyst" == "Data Analyst"
df["title_standard"] = (
    df["title_clean"].str.replace(SENIORITY_WORDS, " ", regex=True)
    .str.replace(r"\s+", " ", regex=True).str.strip().str.title()
)
df.loc[df["title_standard"] == "", "title_standard"] = df["title_clean"].str.title()

# Seniority level (from title + experience later)
def seniority_from_title(t: str):
    t = t.lower()
    if re.search(r"\b(intern|trainee|fresher)\b", t): return "Intern / Trainee"
    if re.search(r"\b(head|director|vp|chief|avp)\b", t): return "Leadership"
    if re.search(r"\b(lead|principal|staff|architect|manager)\b", t): return "Lead / Manager"
    if re.search(r"\b(sr|snr|senior)\b", t): return "Senior"
    if re.search(r"\b(jr|junior|associate|asst|assistant)\b", t): return "Junior"
    return None

df["seniority_title"] = df["title"].map(seniority_from_title)

# Tech / Data flags
DATA_ROLES = {"Data Scientist", "Data Engineer", "Data Analyst"}
TECH_ROLES = DATA_ROLES | {"Full Stack Developer", "Frontend Developer", "Backend Developer",
                           "Mobile Developer", "DevOps / Cloud", "QA / Testing", "Cyber Security",
                           "Software Engineer"}
df["is_data_role"] = df["role_family"].isin(DATA_ROLES)
df["is_tech_role"] = df["role_family"].isin(TECH_ROLES)

# ---------------------------------------------------------------- 4. LOCATION NORMALIZATION
CITY_ALIASES = {
    "bangalore": "Bengaluru", "bengaluru": "Bengaluru", "bangalore rural": "Bengaluru",
    "bombay": "Mumbai", "mumbai suburban": "Mumbai", "navi mumbai": "Mumbai", "thane": "Mumbai",
    "mumbai (all areas)": "Mumbai", "madras": "Chennai", "calcutta": "Kolkata",
    "gurgaon": "Gurugram", "gurugram": "Gurugram", "new delhi": "Delhi NCR", "delhi": "Delhi NCR",
    "noida": "Delhi NCR", "greater noida": "Delhi NCR", "ghaziabad": "Delhi NCR",
    "faridabad": "Delhi NCR", "south delhi": "Delhi NCR", "delhi / ncr": "Delhi NCR", "ncr": "Delhi NCR",
    "hyderabad / secunderabad": "Hyderabad", "secunderabad": "Hyderabad", "cyberabad": "Hyderabad",
    "pune": "Pune", "mohali": "Chandigarh", "kharar": "Chandigarh", "zirakpur": "Chandigarh",
    "panchkula": "Chandigarh", "trivandrum": "Thiruvananthapuram", "cochin": "Kochi",
    "mysore": "Mysuru", "baroda": "Vadodara", "vizag": "Visakhapatnam",
}
# Gurugram stays in "Delhi NCR" for the metro roll-up, but we keep the raw city too
METRO_ROLLUP = {
    "Gurugram": "Delhi NCR",
}


def split_location(loc: str):
    """Return (work_mode, primary_city, n_cities)."""
    s = loc.strip()
    mode = "On-site"
    low = s.lower()
    if low.startswith("hybrid"):
        mode = "Hybrid"
    elif low.startswith("remote") or "work from home" in low or low.startswith("wfh"):
        mode = "Remote"
    elif "remote" in low:
        mode = "Remote"
    s = re.sub(r"^(hybrid|remote|temp\. wfh)\s*[-:]?\s*", "", s, flags=re.I)
    s = re.sub(r"\(.*?\)", "", s).strip()
    parts = [p.strip() for p in re.split(r",|/|\|", s) if p.strip()]
    if not parts:
        return mode, "Remote / Unspecified" if mode == "Remote" else "Unspecified", 0
    first = parts[0]
    key = first.lower()
    city = CITY_ALIASES.get(key, first.title())
    return mode, city, len(parts)


loc_parts = df["location"].map(split_location)
df["work_mode"] = loc_parts.map(lambda x: x[0])
df["city_raw"] = loc_parts.map(lambda x: x[1])
df["n_locations_listed"] = loc_parts.map(lambda x: x[2])
df["city"] = df["city_raw"].replace(METRO_ROLLUP)
# Pure "Remote" rows
df.loc[df["city"].isin(["Remote", "Work From Home", "Wfh"]), "city"] = "Remote / Unspecified"

# Tier classification
TIER1 = {"Bengaluru", "Mumbai", "Delhi NCR", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad"}
TIER2 = {"Jaipur", "Lucknow", "Chandigarh", "Kochi", "Coimbatore", "Indore", "Nagpur", "Vadodara", "Surat",
         "Bhopal", "Visakhapatnam", "Thiruvananthapuram", "Mysuru", "Bhubaneswar", "Patna", "Nashik",
         "Ranchi", "Raipur", "Guwahati", "Dehradun", "Mangaluru", "Madurai", "Vijayawada", "Kanpur",
         "Agra", "Ludhiana", "Amritsar", "Jodhpur", "Udaipur", "Rajkot", "Goa"}


def tier(c):
    if c in TIER1: return "Tier 1"
    if c in TIER2: return "Tier 2"
    if c.startswith("Remote") or c == "Unspecified": return "Remote / Unspecified"
    return "Other"


df["city_tier"] = df["city"].map(tier)
_top = df["city"].value_counts().head(40).index
df["city_group"] = np.where(df["city"].isin(_top), df["city"], "Other Cities")

# ---------------------------------------------------------------- 5. SALARY
for c in ["minimumSalary", "maximumSalary", "minimumExperience", "maximumExperience",
          "ReviewsCount", "AggregateRating"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df["salary_disclosed"] = df["salary"].str.strip().str.lower().ne("not disclosed") & (df["maximumSalary"] > 0)
df["is_unpaid"] = df["salary"].str.strip().str.lower().eq("unpaid")

# USD rows -> INR (assumption: 1 USD = 83 INR, documented in README)
USD_INR = 83
usd = df["currency"].eq("USD")
for c in ["minimumSalary", "maximumSalary"]:
    df.loc[usd & df[c].gt(0), c] = df.loc[usd & df[c].gt(0), c] * USD_INR

sal = df["salary_disclosed"]
df["salary_min_inr"] = df["minimumSalary"].where(sal)
df["salary_max_inr"] = df["maximumSalary"].where(sal)

# sanity: swap if min > max
swap = df["salary_min_inr"] > df["salary_max_inr"]
df.loc[swap, ["salary_min_inr", "salary_max_inr"]] = df.loc[swap, ["salary_max_inr", "salary_min_inr"]].values
log["salary_min_max_swapped"] = int(swap.sum())

df["salary_mid_inr"] = (df["salary_min_inr"] + df["salary_max_inr"]) / 2
df["salary_mid_lpa"] = (df["salary_mid_inr"] / 1e5).round(2)

# Outlier handling: INR annual salary midpoint outside 1.2L - 1.5Cr treated as invalid (monthly figure / typo)
bad = df["salary_mid_inr"].notna() & ((df["salary_mid_inr"] < 120_000) | (df["salary_mid_inr"] > 15_000_000))
log["salary_outliers_nullified"] = int(bad.sum())
for c in ["salary_min_inr", "salary_max_inr", "salary_mid_inr", "salary_mid_lpa"]:
    df.loc[bad, c] = np.nan
df["salary_disclosed"] = df["salary_mid_inr"].notna()

df["salary_band"] = pd.cut(
    df["salary_mid_lpa"],
    bins=[0, 3, 6, 10, 15, 25, 50, 1000],
    labels=["<3 LPA", "3-6 LPA", "6-10 LPA", "10-15 LPA", "15-25 LPA", "25-50 LPA", "50+ LPA"],
).astype("object")

# ---------------------------------------------------------------- 6. EXPERIENCE
df["exp_min_yrs"] = df["minimumExperience"]
df["exp_max_yrs"] = df["maximumExperience"]
df["exp_mid_yrs"] = (df["exp_min_yrs"] + df["exp_max_yrs"]) / 2
df.loc[(df["exp_max_yrs"] > 40) | (df["exp_min_yrs"] > df["exp_max_yrs"]), ["exp_min_yrs", "exp_max_yrs", "exp_mid_yrs"]] = np.nan

def exp_band(x):
    if pd.isna(x): return "Not specified"
    if x < 1: return "Fresher (0-1)"
    if x < 3: return "Junior (1-3)"
    if x < 6: return "Mid (3-6)"
    if x < 10: return "Senior (6-10)"
    return "Lead / Expert (10+)"


df["experience_level"] = df["exp_min_yrs"].map(exp_band)

# ---------------------------------------------------------------- 7. POSTING AGE
def days_ago(s: str):
    s = str(s).lower()
    if any(k in s for k in ["just now", "few hours", "today"]): return 0
    m = re.search(r"(\d+)\s*day", s)
    if m: return int(m.group(1))
    return np.nan


df["days_since_posted"] = df["jobUploaded"].map(days_ago)
df["is_future_start"] = df["jobUploaded"].str.lower().str.startswith("starts")
# Snapshot date of the dataset (jobIds look like DDMMYY... -> 27-Sep-2025 newest)
SNAPSHOT = pd.Timestamp("2025-10-03")
df["posted_date"] = SNAPSHOT - pd.to_timedelta(df["days_since_posted"], unit="D")
# More precise: jobId starts with DDMMYY (validated: jobId date + "N days ago" = 2025-10-03 for 75% of rows)
_id_date = pd.to_datetime(df["jobId"].str[:6], format="%d%m%y", errors="coerce")
_ok = _id_date.between("2025-01-01", SNAPSHOT) & ~df["is_future_start"]
log["posted_date_from_jobid"] = int(_ok.sum())
df["posted_date"] = df["posted_date"].where(~_ok, _id_date)
df.loc[_ok, "days_since_posted"] = (SNAPSHOT - _id_date[_ok]).dt.days

# ---------------------------------------------------------------- 8. SKILLS
SKILL_ALIASES = {
    "ms excel": "Excel", "microsoft excel": "Excel", "advanced excel": "Excel", "excel": "Excel",
    "ms-excel": "Excel", "power bi": "Power BI", "powerbi": "Power BI", "power-bi": "Power BI",
    "ms power bi": "Power BI", "tableau": "Tableau", "sql": "SQL", "mysql": "MySQL", "my sql": "MySQL",
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "pl/sql": "PL/SQL", "plsql": "PL/SQL",
    "t-sql": "SQL Server", "ms sql server": "SQL Server", "sql server": "SQL Server", "mssql": "SQL Server",
    "python": "Python", "python programming": "Python", "python development": "Python",
    "pyspark": "PySpark", "py spark": "PySpark", "apache spark": "Spark", "spark": "Spark",
    "machine learning": "Machine Learning", "ml": "Machine Learning", "deep learning": "Deep Learning",
    "artificial intelligence": "AI", "ai": "AI", "generative ai": "Generative AI", "genai": "Generative AI",
    "gen ai": "Generative AI", "natural language processing": "NLP", "nlp": "NLP", "llm": "LLM",
    "data analysis": "Data Analysis", "data analytics": "Data Analytics", "data science": "Data Science",
    "data visualization": "Data Visualization", "data visualisation": "Data Visualization",
    "data modeling": "Data Modeling", "data modelling": "Data Modeling",
    "data engineering": "Data Engineering", "data warehousing": "Data Warehousing",
    "data warehouse": "Data Warehousing", "etl": "ETL", "etl testing": "ETL Testing",
    "amazon web services": "AWS", "aws": "AWS", "microsoft azure": "Azure", "azure": "Azure",
    "google cloud platform": "GCP", "gcp": "GCP", "gcp cloud": "GCP", "azure databricks": "Databricks",
    "databricks": "Databricks", "snowflake": "Snowflake", "big data": "Big Data", "hadoop": "Hadoop",
    "java": "Java", "core java": "Java", "javascript": "JavaScript", "js": "JavaScript",
    "typescript": "TypeScript", "react": "React", "reactjs": "React", "react js": "React",
    "react.js": "React", "angular": "Angular", "angularjs": "Angular", "node.js": "Node.js",
    "nodejs": "Node.js", "node js": "Node.js", "spring boot": "Spring Boot", "springboot": "Spring Boot",
    "c++": "C++", "c#": "C#", ".net": ".NET", "dotnet": ".NET", "asp.net": "ASP.NET",
    "html": "HTML", "html5": "HTML", "css": "CSS", "css3": "CSS", "git": "Git", "github": "Git",
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes", "jenkins": "Jenkins",
    "ci/cd": "CI/CD", "devops": "DevOps", "linux": "Linux", "r": "R", "sas": "SAS", "dax": "DAX",
    "power query": "Power Query", "looker": "Looker", "qlik": "Qlik", "qlikview": "Qlik",
    "qlik sense": "Qlik", "statistics": "Statistics", "statistical analysis": "Statistics",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch", "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn", "pandas": "Pandas", "numpy": "NumPy", "mongodb": "MongoDB",
    "oracle": "Oracle", "nosql": "NoSQL", "kafka": "Kafka", "airflow": "Airflow",
    "communication skills": "Communication", "communication": "Communication",
    "good communication skills": "Communication", "english": "English",
    "spoken english": "English", "fluent english": "English", "good english communication": "English",
    "sales": "Sales", "business development": "Business Development", "lead generation": "Lead Generation",
    "customer service": "Customer Service", "customer support": "Customer Support",
    "digital marketing": "Digital Marketing", "seo": "SEO", "social media marketing": "Social Media Marketing",
    "recruitment": "Recruitment", "talent acquisition": "Talent Acquisition",
    "accounting": "Accounting", "tally": "Tally", "gst": "GST", "taxation": "Taxation",
    "selenium": "Selenium", "manual testing": "Manual Testing", "automation testing": "Automation Testing",
    "api testing": "API Testing", "rest api": "REST API", "restful api": "REST API", "rest apis": "REST API",
    "microservices": "Microservices", "sap": "SAP", "salesforce": "Salesforce", "jira": "Jira",
    "agile": "Agile", "scrum": "Scrum", "business analysis": "Business Analysis",
    "business intelligence": "Business Intelligence", "bi": "Business Intelligence",
    "reporting": "Reporting", "dashboards": "Dashboards", "dashboard": "Dashboards",
    "rest": "REST API", "restful": "REST API", "web services": "Web Services",
    "aiml": "Machine Learning", "ai/ml": "Machine Learning", "ai ml": "Machine Learning",
    "ssis": "SSIS", "ssrs": "SSRS", "ssas": "SSAS", "informatica": "Informatica",
}


def norm_skill(s: str) -> str:
    s0 = re.sub(r"\s+", " ", s.strip())
    k = s0.lower()
    if k in SKILL_ALIASES:
        return SKILL_ALIASES[k]
    return s0.title() if len(s0) > 3 else s0.upper()


skill_rows = []
tags = df[["jobId", "tagsAndSkills"]].copy()
tags["skill_list"] = tags["tagsAndSkills"].fillna("").str.split(",")
tags = tags.explode("skill_list")
tags["skill_list"] = tags["skill_list"].fillna("").str.strip()
tags = tags[tags["skill_list"].str.len().between(2, 40)]
tags["skill"] = tags["skill_list"].map(norm_skill)
# Drop generic Naukri auto-tags that are not real skills
GENERIC_TAGS = {"Data", "Management", "Development", "Computer Science", "Training", "Operations",
                "Consulting", "Finance", "Team Management", "Team Handling", "Analytical", "Usage",
                "Performance", "Acquisition", "Sr", "Skills", "Business", "Technical", "Engineering",
                "Software", "Technology", "It", "Executive", "Manager", "Process", "Support",
                "Application Development", "Software Development", "Continuous Integration", "Architecture"}
n_before = len(tags)
tags = tags[~tags["skill"].isin(GENERIC_TAGS)]
log["generic_skill_tags_dropped"] = int(n_before - len(tags))
tags = tags[["jobId", "skill"]].drop_duplicates()
log["skill_rows"] = len(tags)
log["distinct_skills"] = int(tags["skill"].nunique())

df["n_skills"] = df["jobId"].map(tags.groupby("jobId").size()).fillna(0).astype(int)

# ---------------------------------------------------------------- 9. COMPANY / RATINGS
df["company_clean"] = (df["companyName"].str.replace(r"\b(pvt\.?|private|ltd\.?|limited|llp|inc\.?|india|technologies|technology|solutions|services|consulting|consultancy)\b",
                                                      " ", regex=True, case=False)
                       .str.replace(r"[,.]", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
                       .str.replace(r"(?i)\s+(and|&)$", "", regex=True))
df.loc[df["company_clean"] == "", "company_clean"] = df["companyName"]
df["company_clean"] = df["company_clean"].str.title()
df["rating"] = df["AggregateRating"].where(df["AggregateRating"].between(1, 5))
df["review_count"] = df["ReviewsCount"]

# ---------------------------------------------------------------- 10. FINAL COLUMNS
df["job_description_short"] = (df["jobDescription"].str.replace(r"<[^>]+>", " ", regex=True)
                               .str.replace(r"\s+", " ", regex=True).str.strip().str[:300])

final_cols = [
    "jobId", "title", "title_standard", "role_family", "is_data_role", "is_tech_role", "seniority_title",
    "companyId", "companyName", "company_clean", "rating", "review_count",
    "location", "city", "city_group", "city_raw", "city_tier", "work_mode", "n_locations_listed",
    "experience", "exp_min_yrs", "exp_max_yrs", "exp_mid_yrs", "experience_level",
    "salary", "salary_disclosed", "is_unpaid", "salary_min_inr", "salary_max_inr", "salary_mid_inr",
    "salary_mid_lpa", "salary_band", "currency",
    "jobUploaded", "days_since_posted", "posted_date", "is_future_start",
    "n_skills", "job_description_short",
]
clean = df[final_cols].rename(columns={"jobId": "job_id", "companyId": "company_id"})
clean.to_csv("data/clean_jobs.csv", index=False)
tags.rename(columns={"jobId": "job_id"}).to_csv("data/job_skills.csv", index=False)

log["clean_rows"] = len(clean)
log["rows_removed_total"] = log["raw_rows"] - log["clean_rows"]
log["salary_disclosed_pct"] = round(clean["salary_disclosed"].mean() * 100, 1)
log["data_roles"] = int(clean["is_data_role"].sum())
log["tech_roles"] = int(clean["is_tech_role"].sum())
log["distinct_titles_raw"] = int(df["title"].nunique())
log["distinct_titles_standard"] = int(df["title_standard"].nunique())
log["distinct_locations_raw"] = int(df["location"].nunique())
log["distinct_cities_clean"] = int(df["city"].nunique())
log["role_family_counts"] = clean["role_family"].value_counts().to_dict()
with open("data/cleaning_log.json", "w") as f:
    json.dump(log, f, indent=2)
print(json.dumps({k: v for k, v in log.items() if k != "role_family_counts"}, indent=2))
print(clean["role_family"].value_counts().head(25))
print(clean["city"].value_counts().head(20))
