-- =====================================================================
-- INDIAN JOB MARKET INTELLIGENCE 2025  |  SQL ANALYSIS (SQLite dialect)
-- Tables loaded by 02_sql_analysis.py:
--   jobs        (one row per cleaned job posting)
--   job_skills  (job_id, skill)  -> one row per job-skill pair
-- Each query is tagged  -- [Q##] name  and is exported to outputs/sql_results/
-- =====================================================================

-- ---------------------------------------------------------------------
-- PART A : STAR-SCHEMA VIEWS (used by the Power BI model)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_salary_jobs;
CREATE VIEW v_salary_jobs AS
SELECT * FROM jobs WHERE salary_disclosed = 1;

DROP VIEW IF EXISTS v_data_jobs;
CREATE VIEW v_data_jobs AS
SELECT * FROM jobs WHERE is_data_role = 1;

-- ---------------------------------------------------------------------
-- PART B : DATA QUALITY CHECKS
-- ---------------------------------------------------------------------
-- [Q01] data_quality_summary
SELECT
    COUNT(*)                                             AS total_jobs,
    COUNT(DISTINCT job_id)                               AS distinct_job_ids,
    COUNT(DISTINCT company_clean)                        AS distinct_companies,
    COUNT(DISTINCT city)                                 AS distinct_cities,
    COUNT(DISTINCT title_standard)                       AS distinct_standard_titles,
    ROUND(100.0 * SUM(salary_disclosed) / COUNT(*), 1)   AS pct_salary_disclosed,
    ROUND(100.0 * SUM(CASE WHEN experience_level = 'Not specified' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_experience_missing,
    ROUND(100.0 * SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_company_rating_missing
FROM jobs;

-- ---------------------------------------------------------------------
-- PART C : ROLES
-- ---------------------------------------------------------------------
-- [Q02] role_family_demand_rank
SELECT
    role_family,
    COUNT(*)                                               AS job_postings,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM jobs), 2) AS pct_of_market,
    RANK() OVER (ORDER BY COUNT(*) DESC)                   AS demand_rank
FROM jobs
GROUP BY role_family
ORDER BY job_postings DESC;

-- [Q03] top_standard_titles_data_roles
SELECT
    title_standard,
    role_family,
    COUNT(*) AS job_postings
FROM v_data_jobs
GROUP BY title_standard, role_family
ORDER BY job_postings DESC
LIMIT 25;

-- ---------------------------------------------------------------------
-- PART D : SKILLS
-- ---------------------------------------------------------------------
-- [Q04] top_skills_overall
SELECT
    s.skill,
    COUNT(*)                                                            AS job_postings,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM jobs), 2)            AS pct_of_all_jobs,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC)                          AS skill_rank
FROM job_skills s
GROUP BY s.skill
ORDER BY job_postings DESC
LIMIT 30;

-- [Q05] top_skills_data_roles   (the headline insight of the project)
SELECT
    s.skill,
    COUNT(*)                                                                    AS job_postings,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM v_data_jobs), 2)             AS pct_of_data_jobs,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC)                                  AS skill_rank
FROM job_skills s
JOIN v_data_jobs j ON j.job_id = s.job_id
GROUP BY s.skill
HAVING COUNT(*) >= 20
ORDER BY job_postings DESC
LIMIT 30;

-- [Q06] top_skills_by_data_role  (top 10 per role family using window ranking)
WITH ranked AS (
    SELECT
        j.role_family,
        s.skill,
        COUNT(*) AS job_postings,
        ROW_NUMBER() OVER (PARTITION BY j.role_family ORDER BY COUNT(*) DESC) AS rn
    FROM job_skills s
    JOIN v_data_jobs j ON j.job_id = s.job_id
    GROUP BY j.role_family, s.skill
)
SELECT role_family, rn AS rank_in_role, skill, job_postings
FROM ranked
WHERE rn <= 10
ORDER BY role_family, rn;

-- [Q07] skill_co_occurrence_with_sql_data_roles
SELECT
    b.skill                       AS paired_skill,
    COUNT(*)                      AS jobs_with_sql_and_skill
FROM job_skills a
JOIN job_skills b ON a.job_id = b.job_id AND a.skill <> b.skill
JOIN v_data_jobs j ON j.job_id = a.job_id
WHERE a.skill = 'SQL'
GROUP BY b.skill
ORDER BY jobs_with_sql_and_skill DESC
LIMIT 15;

-- [Q08] skill_salary_premium_data_roles
-- median salary (LPA) of data jobs listing the skill vs data jobs that do not
WITH sal AS (
    SELECT job_id, salary_mid_lpa FROM v_data_jobs WHERE salary_disclosed = 1
),
base AS (
    SELECT AVG(salary_mid_lpa) AS avg_all FROM sal
),
sk AS (
    SELECT s.skill, COUNT(*) AS n_with_salary, AVG(sal.salary_mid_lpa) AS avg_lpa
    FROM job_skills s JOIN sal ON sal.job_id = s.job_id
    GROUP BY s.skill
    HAVING COUNT(*) >= 15
)
SELECT
    sk.skill,
    sk.n_with_salary,
    ROUND(sk.avg_lpa, 2)                                          AS avg_salary_lpa,
    ROUND(base.avg_all, 2)                                        AS data_roles_avg_lpa,
    ROUND(100.0 * (sk.avg_lpa - base.avg_all) / base.avg_all, 1)  AS premium_pct
FROM sk CROSS JOIN base
ORDER BY premium_pct DESC
LIMIT 25;

-- ---------------------------------------------------------------------
-- PART E : LOCATIONS
-- ---------------------------------------------------------------------
-- [Q09] city_demand_all_jobs
SELECT
    city_group                                         AS city,
    COUNT(*)                                           AS job_postings,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM jobs), 2) AS pct_of_market,
    SUM(is_tech_role)                                  AS tech_jobs,
    SUM(is_data_role)                                  AS data_jobs
FROM jobs
WHERE city_group <> 'Other Cities'
GROUP BY city_group
ORDER BY job_postings DESC
LIMIT 20;

-- [Q10] data_jobs_by_city_with_salary
SELECT
    city_group                                         AS city,
    COUNT(*)                                           AS data_job_postings,
    SUM(salary_disclosed)                              AS with_salary,
    ROUND(AVG(salary_mid_lpa), 2)                      AS avg_salary_lpa
FROM v_data_jobs
WHERE city_group NOT IN ('Other Cities', 'Remote / Unspecified')
GROUP BY city_group
HAVING COUNT(*) >= 10
ORDER BY data_job_postings DESC;

-- [Q11] work_mode_split_by_role_group
SELECT
    CASE WHEN is_data_role = 1 THEN 'Data roles'
         WHEN is_tech_role = 1 THEN 'Other tech roles'
         ELSE 'Non-tech roles' END                      AS role_group,
    work_mode,
    COUNT(*)                                            AS job_postings,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY
        CASE WHEN is_data_role = 1 THEN 'Data roles'
             WHEN is_tech_role = 1 THEN 'Other tech roles'
             ELSE 'Non-tech roles' END), 2)             AS pct_within_group
FROM jobs
GROUP BY role_group, work_mode
ORDER BY role_group, job_postings DESC;

-- [Q12] city_tier_mix
SELECT city_tier, COUNT(*) AS job_postings,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM jobs), 2) AS pct,
       SUM(is_data_role) AS data_jobs
FROM jobs
GROUP BY city_tier
ORDER BY job_postings DESC;

-- ---------------------------------------------------------------------
-- PART F : SALARY
-- ---------------------------------------------------------------------
-- [Q13] salary_by_role_family  (true median via window functions)
WITH ranked AS (
    SELECT
        role_family,
        salary_mid_lpa,
        ROW_NUMBER() OVER (PARTITION BY role_family ORDER BY salary_mid_lpa) AS rn,
        COUNT(*)     OVER (PARTITION BY role_family)                         AS cnt
    FROM v_salary_jobs
),
med AS (
    SELECT role_family, ROUND(AVG(salary_mid_lpa), 2) AS median_lpa
    FROM ranked
    WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
    GROUP BY role_family
)
SELECT
    j.role_family,
    COUNT(*)                          AS jobs_with_salary,
    ROUND(AVG(j.salary_mid_lpa), 2)   AS avg_lpa,
    m.median_lpa,
    ROUND(MIN(j.salary_min_inr) / 1e5, 2) AS min_lpa,
    ROUND(MAX(j.salary_max_inr) / 1e5, 2) AS max_lpa
FROM v_salary_jobs j
JOIN med m ON m.role_family = j.role_family
GROUP BY j.role_family
HAVING COUNT(*) >= 30
ORDER BY m.median_lpa DESC;

-- [Q14] data_role_salary_by_experience
SELECT
    role_family,
    experience_level,
    COUNT(*)                        AS jobs_with_salary,
    ROUND(AVG(salary_mid_lpa), 2)   AS avg_salary_lpa
FROM v_data_jobs
WHERE salary_disclosed = 1 AND experience_level <> 'Not specified'
GROUP BY role_family, experience_level
HAVING COUNT(*) >= 5
ORDER BY role_family,
         CASE experience_level
             WHEN 'Fresher (0-1)' THEN 1 WHEN 'Junior (1-3)' THEN 2 WHEN 'Mid (3-6)' THEN 3
             WHEN 'Senior (6-10)' THEN 4 ELSE 5 END;

-- [Q15] salary_band_distribution_data_vs_all
SELECT
    salary_band,
    SUM(CASE WHEN is_data_role = 1 THEN 1 ELSE 0 END)          AS data_jobs,
    COUNT(*)                                                   AS all_jobs,
    ROUND(100.0 * SUM(CASE WHEN is_data_role = 1 THEN 1 ELSE 0 END)
          / NULLIF((SELECT COUNT(*) FROM v_data_jobs WHERE salary_disclosed = 1), 0), 2) AS pct_of_data_jobs
FROM v_salary_jobs
GROUP BY salary_band
ORDER BY CASE salary_band
    WHEN '<3 LPA' THEN 1 WHEN '3-6 LPA' THEN 2 WHEN '6-10 LPA' THEN 3 WHEN '10-15 LPA' THEN 4
    WHEN '15-25 LPA' THEN 5 WHEN '25-50 LPA' THEN 6 ELSE 7 END;

-- [Q16] salary_by_city_tech_roles
SELECT
    city_group                       AS city,
    COUNT(*)                         AS tech_jobs_with_salary,
    ROUND(AVG(salary_mid_lpa), 2)    AS avg_salary_lpa
FROM v_salary_jobs
WHERE is_tech_role = 1 AND city_group NOT IN ('Other Cities', 'Remote / Unspecified')
GROUP BY city_group
HAVING COUNT(*) >= 30
ORDER BY avg_salary_lpa DESC;

-- ---------------------------------------------------------------------
-- PART G : EXPERIENCE & COMPANIES
-- ---------------------------------------------------------------------
-- [Q17] experience_demand_data_roles
SELECT
    experience_level,
    COUNT(*)                                                           AS data_jobs,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM v_data_jobs), 2)    AS pct
FROM v_data_jobs
GROUP BY experience_level
ORDER BY CASE experience_level
    WHEN 'Fresher (0-1)' THEN 1 WHEN 'Junior (1-3)' THEN 2 WHEN 'Mid (3-6)' THEN 3
    WHEN 'Senior (6-10)' THEN 4 WHEN 'Lead / Expert (10+)' THEN 5 ELSE 6 END;

-- [Q18] top_companies_hiring_data_roles
SELECT
    company_clean                                   AS company,
    COUNT(*)                                        AS data_job_postings,
    ROUND(AVG(salary_mid_lpa), 2)                   AS avg_salary_lpa,
    ROUND(AVG(rating), 2)                           AS avg_company_rating
FROM v_data_jobs
WHERE company_clean <> 'Unknown'
GROUP BY company_clean
ORDER BY data_job_postings DESC
LIMIT 20;

-- [Q19] skills_demanded_by_experience_level_data_roles
WITH t AS (
    SELECT j.experience_level, s.skill, COUNT(*) AS n,
           ROW_NUMBER() OVER (PARTITION BY j.experience_level ORDER BY COUNT(*) DESC) AS rn
    FROM job_skills s JOIN v_data_jobs j ON j.job_id = s.job_id
    WHERE j.experience_level <> 'Not specified'
    GROUP BY j.experience_level, s.skill
)
SELECT experience_level, rn AS rank_in_level, skill, n AS job_postings
FROM t WHERE rn <= 8
ORDER BY experience_level, rn;

-- [Q20] posting_recency_by_role_group
SELECT
    CASE WHEN is_data_role = 1 THEN 'Data roles' WHEN is_tech_role = 1 THEN 'Other tech roles' ELSE 'Non-tech roles' END AS role_group,
    ROUND(AVG(days_since_posted), 2) AS avg_days_since_posted,
    SUM(CASE WHEN days_since_posted <= 3 THEN 1 ELSE 0 END) AS posted_last_3_days,
    COUNT(*) AS jobs
FROM jobs
GROUP BY role_group;
