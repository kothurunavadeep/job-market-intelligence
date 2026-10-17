"""
Step 3 - POWER BI DATA MODEL
Builds a star schema (CSV files) ready to import into Power BI Desktop.

  fact_jobs          1 row / job posting
  fact_job_skills    1 row / job-skill pair  (bridge, many-to-many)
  dim_skill          skill + category
  dim_role           role family + group
  dim_city           city + tier + state-ish region + lat/long of top cities
  dim_company        company + avg rating
  dim_experience     experience level + sort order
  dim_salary_band    salary band + sort order
  dim_date           calendar for posted_date
"""
import os
import pandas as pd
import numpy as np

OUT = "outputs/powerbi/data"
os.makedirs(OUT, exist_ok=True)

jobs = pd.read_csv("data/clean_jobs.csv", parse_dates=["posted_date"])
skills = pd.read_csv("data/job_skills.csv")

# ------------------------------------------------------------------ dim_skill
CAT = {
    "Programming": ["Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "R", "Scala", "Go", "PHP", ".NET",
                    "ASP.NET", "Node.js", "Kotlin", "Swift", "SAS", "Shell Scripting", "Ruby", "Perl"],
    "Database & SQL": ["SQL", "MySQL", "PostgreSQL", "PL/SQL", "SQL Server", "Oracle", "MongoDB", "NoSQL",
                       "Data Modeling", "Data Warehousing", "Redshift", "Teradata", "Cassandra", "Redis"],
    "BI & Visualization": ["Power BI", "Tableau", "Excel", "Looker", "Qlik", "DAX", "Power Query",
                           "Data Visualization", "Business Intelligence", "Dashboards", "Reporting", "SSRS",
                           "SSAS", "Google Data Studio", "Advanced Excel"],
    "Big Data & Engineering": ["PySpark", "Spark", "Hadoop", "Hive", "Kafka", "Airflow", "ETL", "Databricks",
                               "Snowflake", "Big Data", "Data Engineering", "Informatica", "SSIS", "ETL Testing",
                               "Talend", "DBT", "Data Pipelines", "Data Architecture"],
    "Machine Learning & AI": ["Machine Learning", "Deep Learning", "AI", "Generative AI", "NLP", "LLM",
                              "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Computer Vision",
                              "Data Science", "Statistics", "Langchain", "Aiml", "Data Analysis", "Data Analytics",
                              "Statistical Modeling", "Predictive Modeling", "Mlops"],
    "Cloud & DevOps": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "CI/CD", "DevOps", "Linux",
                       "Terraform", "Git", "Ansible", "Cloud"],
    "Web & App Development": ["HTML", "CSS", "React", "Angular", "Spring Boot", "REST API", "Microservices",
                              "Web Services", "Vue.Js", "Django", "Flask", "Android", "Ios", "Flutter"],
    "Testing & QA": ["Selenium", "Manual Testing", "Automation Testing", "API Testing", "Software Testing",
                     "Test Automation", "Jira"],
    "Enterprise Software": ["SAP", "Salesforce", "ERP", "Servicenow", "Workday", "Peoplesoft"],
    "Sales & Marketing": ["Sales", "Business Development", "Lead Generation", "B2B Sales", "Channel Sales",
                          "Field Sales", "Marketing", "Digital Marketing", "SEO", "Social Media Marketing",
                          "Customer Service", "Customer Support", "Voice Process", "BPO"],
    "Finance & HR": ["Accounting", "Tally", "GST", "Taxation", "Compliance", "Recruitment", "Talent Acquisition"],
    "Soft Skills & Process": ["Communication", "English", "Agile", "Scrum", "Project Management",
                              "Troubleshooting", "Automation", "Business Analysis"],
}
cat_lookup = {s: c for c, lst in CAT.items() for s in lst}
dim_skill = pd.DataFrame({"skill": skills["skill"].unique()})
dim_skill["skill_category"] = dim_skill["skill"].map(cat_lookup).fillna("Other")
dim_skill["is_core_data_skill"] = dim_skill["skill"].isin(
    ["Python", "SQL", "Power BI", "Tableau", "Excel", "R", "Machine Learning", "PySpark", "Spark", "ETL",
     "AWS", "Azure", "GCP", "Snowflake", "Databricks", "Data Analysis", "Statistics", "Data Visualization",
     "Hadoop", "Hive", "Scala", "Looker", "Qlik", "DAX", "Deep Learning", "NLP", "Generative AI"]).astype(int)
dim_skill.insert(0, "skill_id", range(1, len(dim_skill) + 1))

# keep only skills that appear in >= 5 jobs to keep the model light (long tail of typos)
cnt = skills["skill"].value_counts()
keep = cnt[cnt >= 5].index
skills_f = skills[skills["skill"].isin(keep)]
dim_skill = dim_skill[dim_skill["skill"].isin(keep)].reset_index(drop=True)
dim_skill["skill_id"] = range(1, len(dim_skill) + 1)
fact_skills = skills_f.merge(dim_skill[["skill", "skill_id"]], on="skill")[["job_id", "skill_id"]]

# ------------------------------------------------------------------ dim_role
role_group = {
    "Data Analyst": "Data", "Data Scientist": "Data", "Data Engineer": "Data",
    "Software Engineer": "Tech", "Backend Developer": "Tech", "Frontend Developer": "Tech",
    "Full Stack Developer": "Tech", "Mobile Developer": "Tech", "DevOps / Cloud": "Tech",
    "QA / Testing": "Tech", "Cyber Security": "Tech",
}
dim_role = pd.DataFrame({"role_family": sorted(jobs["role_family"].unique())})
dim_role["role_group"] = dim_role["role_family"].map(role_group).fillna("Non-Tech")
dim_role.insert(0, "role_id", range(1, len(dim_role) + 1))

# ------------------------------------------------------------------ dim_city
COORDS = {
    "Bengaluru": (12.9716, 77.5946), "Hyderabad": (17.3850, 78.4867), "Delhi NCR": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777), "Pune": (18.5204, 73.8567), "Chennai": (13.0827, 80.2707),
    "Ahmedabad": (23.0225, 72.5714), "Kolkata": (22.5726, 88.3639), "Chandigarh": (30.7333, 76.7794),
    "Kochi": (9.9312, 76.2673), "Jaipur": (26.9124, 75.7873), "Coimbatore": (11.0168, 76.9558),
    "Vadodara": (22.3072, 73.1812), "Nagpur": (21.1458, 79.0882), "Surat": (21.1702, 72.8311),
    "Lucknow": (26.8467, 80.9462), "Nashik": (19.9975, 73.7898), "Ludhiana": (30.9010, 75.8573),
    "Udaipur": (24.5854, 73.7125), "Indore": (22.7196, 75.8577), "Bhopal": (23.2599, 77.4126),
    "Thiruvananthapuram": (8.5241, 76.9366), "Visakhapatnam": (17.6868, 83.2185),
    "Bhubaneswar": (20.2961, 85.8245), "Mysuru": (12.2958, 76.6394), "Patna": (25.5941, 85.1376),
    "Guwahati": (26.1445, 91.7362), "Dehradun": (30.3165, 78.0322), "Ranchi": (23.3441, 85.3096),
    "Raipur": (21.2514, 81.6296), "Mangaluru": (12.9141, 74.8560), "Madurai": (9.9252, 78.1198),
    "Vijayawada": (16.5062, 80.6480), "Kanpur": (26.4499, 80.3319), "Agra": (27.1767, 78.0081),
    "Jodhpur": (26.2389, 73.0243), "Rajkot": (22.3039, 70.8022), "Goa": (15.2993, 74.1240),
    "Amritsar": (31.6340, 74.8723), "Thane": (19.2183, 72.9781),
}
dim_city = (jobs.groupby(["city_group", "city_tier"]).size().reset_index(name="_n")
            .sort_values("_n", ascending=False).drop_duplicates("city_group").drop(columns="_n"))
dim_city = dim_city.rename(columns={"city_group": "city"})
dim_city["latitude"] = dim_city["city"].map(lambda c: COORDS.get(c, (np.nan, np.nan))[0])
dim_city["longitude"] = dim_city["city"].map(lambda c: COORDS.get(c, (np.nan, np.nan))[1])
dim_city["country"] = "India"
dim_city.insert(0, "city_id", range(1, len(dim_city) + 1))

# ------------------------------------------------------------------ dim_company
comp = (jobs.groupby("company_clean").agg(company_id=("company_id", "first"),
                                          avg_rating=("rating", "mean"),
                                          max_reviews=("review_count", "max")).reset_index())
comp["avg_rating"] = comp["avg_rating"].round(2)
comp.insert(0, "company_key", range(1, len(comp) + 1))

# ------------------------------------------------------------------ dim_experience / salary band
dim_exp = pd.DataFrame({
    "experience_level": ["Fresher (0-1)", "Junior (1-3)", "Mid (3-6)", "Senior (6-10)", "Lead / Expert (10+)", "Not specified"],
    "sort_order": [1, 2, 3, 4, 5, 6]})
dim_band = pd.DataFrame({
    "salary_band": ["<3 LPA", "3-6 LPA", "6-10 LPA", "10-15 LPA", "15-25 LPA", "25-50 LPA", "50+ LPA"],
    "sort_order": [1, 2, 3, 4, 5, 6, 7]})

# ------------------------------------------------------------------ dim_date
dmin, dmax = jobs["posted_date"].min(), jobs["posted_date"].max()
dates = pd.date_range(dmin, dmax, freq="D")
dim_date = pd.DataFrame({"date": dates})
dim_date["year"] = dim_date["date"].dt.year
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.strftime("%b")
dim_date["day_name"] = dim_date["date"].dt.strftime("%a")
dim_date["day_of_week"] = dim_date["date"].dt.dayofweek + 1
dim_date["week_of_year"] = dim_date["date"].dt.isocalendar().week.astype(int)
dim_date["date"] = dim_date["date"].dt.date

# ------------------------------------------------------------------ fact_jobs
f = jobs.merge(dim_role[["role_family", "role_id"]], on="role_family", how="left")
f = f.merge(dim_city[["city", "city_id"]], left_on="city_group", right_on="city", how="left", suffixes=("", "_dim"))
f = f.merge(comp[["company_clean", "company_key"]], on="company_clean", how="left")
f["posted_date"] = f["posted_date"].dt.date
fact_jobs = f[[
    "job_id", "title", "title_standard", "role_id", "city_id", "company_key", "posted_date",
    "work_mode", "experience_level", "exp_min_yrs", "exp_max_yrs", "salary_band",
    "salary_disclosed", "salary_min_inr", "salary_max_inr", "salary_mid_inr", "salary_mid_lpa",
    "is_data_role", "is_tech_role", "is_unpaid", "n_skills", "rating", "review_count", "seniority_title",
]].copy()
fact_jobs["job_count"] = 1
for c in ["salary_disclosed", "is_data_role", "is_tech_role", "is_unpaid"]:
    fact_jobs[c] = fact_jobs[c].astype(int)

# ------------------------------------------------------------------ write
tables = {
    "fact_jobs": fact_jobs, "fact_job_skills": fact_skills, "dim_skill": dim_skill, "dim_role": dim_role,
    "dim_city": dim_city, "dim_company": comp, "dim_experience": dim_exp, "dim_salary_band": dim_band,
    "dim_date": dim_date,
}
for name, t in tables.items():
    t.to_csv(f"{OUT}/{name}.csv", index=False)
    print(f"{name:18s} {len(t):>8,} rows  x {t.shape[1]} cols")

# integrity checks
assert fact_jobs["job_id"].is_unique
assert fact_jobs["role_id"].notna().all()
assert fact_jobs["city_id"].notna().all(), "city_id nulls"
assert fact_jobs["company_key"].notna().all()
assert set(fact_skills["job_id"]) <= set(fact_jobs["job_id"])
print("Referential integrity OK")
print(dim_skill["skill_category"].value_counts())
