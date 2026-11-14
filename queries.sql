-- ============================================================================
-- SQL-скрипти для розрахунково-графічної роботи (СУБД PostgreSQL / pgAdmin 4)
-- Студент: Кученьов Ілля Дмитрович, група КВ-42, варіант 9 (база даних lab1)
-- ============================================================================

-- 1. Створення таблиць та обмежень цілісності (3НФ)
CREATE TABLE IF NOT EXISTS public.companies (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    contact_email VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS public.candidates (
    candidate_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS public.vacancies (
    vacancy_id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES public.companies(company_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    title VARCHAR(100) NOT NULL,
    salary NUMERIC(10, 2) CHECK (salary IS NULL OR salary > 0),
    description TEXT,
    is_remote BOOLEAN NOT NULL DEFAULT FALSE
);

ALTER TABLE public.vacancies
    ADD COLUMN IF NOT EXISTS is_remote BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS public.resumes (
    resume_id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES public.candidates(candidate_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    title VARCHAR(100) NOT NULL,
    skills TEXT,
    expected_salary NUMERIC(10, 2) CHECK (expected_salary IS NULL OR expected_salary > 0)
);

CREATE TABLE IF NOT EXISTS public.applications (
    application_id SERIAL PRIMARY KEY,
    resume_id INTEGER NOT NULL REFERENCES public.resumes(resume_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    vacancy_id INTEGER NOT NULL REFERENCES public.vacancies(vacancy_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    apply_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'Submitted'
        CHECK (status IN ('Submitted', 'Interview', 'Offer', 'Rejected')),
    UNIQUE (resume_id, vacancy_id)
);

-- 2. Пакетна генерація псевдовипадкових даних засобами SQL (на прикладі 100 000 записів)
-- 2.1. Компанії (companies)
WITH base AS (SELECT COALESCE(MAX(company_id), 0) AS max_id FROM public.companies)
INSERT INTO public.companies (company_name, city, contact_email)
SELECT
    (ARRAY['Soft', 'Tech', 'Cyber', 'Data', 'Cloud', 'Nova', 'Smart', 'Global'])[1 + trunc(random() * 8)::int]
    || ' ' ||
    (ARRAY['Systems', 'Solutions', 'Labs', 'Dynamics', 'Group', 'Hub', 'Vision', 'Works'])[1 + trunc(random() * 8)::int]
    || ' #' || (base.max_id + gs)::text,
    (ARRAY['Київ', 'Львів', 'Харків', 'Дніпро', 'Одеса', 'Вінниця'])[1 + trunc(random() * 6)::int],
    'hr.' || lower(chr(trunc(65 + random() * 25)::int) || chr(trunc(65 + random() * 25)::int))
    || '.' || (base.max_id + gs)::text || '@company.ua'
FROM generate_series(1, 1000) AS gs CROSS JOIN base;

-- 2.2. Кандидати (candidates)
WITH base AS (SELECT COALESCE(MAX(candidate_id), 0) AS max_id FROM public.candidates)
INSERT INTO public.candidates (full_name, email, phone)
SELECT
    (ARRAY['Олександр', 'Ілля', 'Дмитро', 'Максим', 'Артем', 'Марія', 'Анна', 'Софія'])[1 + trunc(random() * 8)::int]
    || ' ' ||
    (ARRAY['Мельник', 'Шевченко', 'Коваленко', 'Бондаренко', 'Бойко', 'Ткаченко', 'Кравченко', 'Коваль'])[1 + trunc(random() * 8)::int],
    'cand.' || lower(chr(trunc(65 + random() * 25)::int) || chr(trunc(65 + random() * 25)::int))
    || '.' || (base.max_id + gs)::text || '@gmail.com',
    '+380' || lpad((500000000 + base.max_id + gs)::text, 9, '0')
FROM generate_series(1, 5000) AS gs CROSS JOIN base;

-- 2.3. Вакансії (vacancies — 100 000 записів)
WITH comp AS (SELECT array_agg(company_id) AS ids, count(*)::int AS cnt FROM public.companies)
INSERT INTO public.vacancies (company_id, title, salary, description, is_remote)
SELECT
    comp.ids[1 + trunc(random() * comp.cnt)::int],
    (ARRAY['Junior', 'Middle', 'Senior', 'Lead'])[1 + trunc(random() * 4)::int]
    || ' ' ||
    (ARRAY['Python Engineer', 'Golang Developer', 'C++ CV Engineer', 'Data Analyst', 'DevOps Engineer', 'DBA'])[1 + trunc(random() * 6)::int],
    round((20000 + random() * 160000)::numeric, 2),
    'Розробка ПЗ, робота з PostgreSQL та оптимізація запитів.',
    (random() >= 0.45)
FROM generate_series(1, 100000) AS gs CROSS JOIN comp
WHERE comp.cnt > 0;

-- 2.4. Резюме (resumes)
WITH cand AS (SELECT array_agg(candidate_id) AS ids, count(*)::int AS cnt FROM public.candidates)
INSERT INTO public.resumes (candidate_id, title, skills, expected_salary)
SELECT
    cand.ids[1 + trunc(random() * cand.cnt)::int],
    (ARRAY['Python / Backend Developer', 'Golang Developer', 'Computer Vision Engineer', 'Data Analyst', 'DevOps Engineer'])[1 + trunc(random() * 5)::int],
    (ARRAY['Python, PostgreSQL, Docker, Git', 'Golang, PostgreSQL, Redis, gRPC', 'C++, Python, OpenCV, PyTorch, SQL', 'SQL, Python, Pandas, PowerBI'])[1 + trunc(random() * 4)::int],
    round((18000 + random() * 142000)::numeric, 2)
FROM generate_series(1, 10000) AS gs CROSS JOIN cand
WHERE cand.cnt > 0;

-- 2.5. Відгуки (applications — 100 000 записів)
WITH r_pool AS (SELECT array_agg(resume_id ORDER BY resume_id) AS ids, count(*)::bigint AS cnt FROM public.resumes),
     v_pool AS (SELECT array_agg(vacancy_id ORDER BY vacancy_id) AS ids, count(*)::bigint AS cnt FROM public.vacancies)
INSERT INTO public.applications (resume_id, vacancy_id, apply_date, status)
SELECT
    r_pool.ids[1 + ((gs - 1) / v_pool.cnt)::int],
    v_pool.ids[1 + ((gs - 1) % v_pool.cnt)::int],
    timestamptz '2025-01-01 08:00:00+02' +
        random() * (timestamptz '2026-11-14 20:00:00+02' - timestamptz '2025-01-01 08:00:00+02'),
    (ARRAY['Submitted', 'Interview', 'Offer', 'Rejected'])[1 + trunc(random() * 4)::int]
FROM generate_series(1, 100000) AS gs CROSS JOIN r_pool CROSS JOIN v_pool
WHERE r_pool.cnt > 0 AND v_pool.cnt > 0 AND gs <= r_pool.cnt * v_pool.cnt
ON CONFLICT (resume_id, vacancy_id) DO NOTHING;

-- 3. Три параметризовані пошукові SQL-запити
-- Запит №1 (2 таблиці: vacancies + companies)
SELECT v.vacancy_id, c.company_name, c.city, v.title, v.salary, v.is_remote, c.contact_email
FROM public.vacancies v
JOIN public.companies c ON v.company_id = c.company_id
WHERE v.salary BETWEEN 30000 AND 120000
  AND v.title ILIKE '%Engineer%'
  AND c.city ILIKE '%Київ%'
  AND v.is_remote = TRUE
ORDER BY v.salary DESC
LIMIT 50;

-- Запит №2 (5 таблиць: applications + resumes + candidates + vacancies + companies)
SELECT a.application_id, cand.full_name, r.title AS resume_title, r.expected_salary,
       comp.company_name, v.title AS vacancy_title,
       to_char(a.apply_date, 'YYYY-MM-DD HH24:MI') AS apply_date, a.status
FROM public.applications a
JOIN public.resumes r       ON a.resume_id = r.resume_id
JOIN public.candidates cand ON r.candidate_id = cand.candidate_id
JOIN public.vacancies v     ON a.vacancy_id = v.vacancy_id
JOIN public.companies comp  ON v.company_id = comp.company_id
WHERE a.apply_date BETWEEN '2025-01-01'::timestamptz AND '2026-12-31'::timestamptz
  AND r.expected_salary BETWEEN 25000 AND 110000
  AND r.skills ILIKE '%PostgreSQL%'
  AND a.status LIKE 'Interview%'
  AND v.is_remote = TRUE
ORDER BY a.apply_date DESC
LIMIT 50;

-- Запит №3 (3 таблиці з агрегуванням GROUP BY та HAVING)
SELECT c.company_id, c.company_name, c.city,
       COUNT(DISTINCT v.vacancy_id) AS vacancies_count,
       COUNT(a.application_id) AS total_applications,
       COUNT(a.application_id) FILTER (WHERE a.status = 'Offer') AS offers_count,
       ROUND(AVG(v.salary), 2) AS avg_salary,
       MAX(v.salary) AS max_salary
FROM public.companies c
JOIN public.vacancies v ON c.company_id = v.company_id
LEFT JOIN public.applications a
       ON v.vacancy_id = a.vacancy_id
      AND a.apply_date BETWEEN '2025-01-01'::timestamptz AND '2026-12-31'::timestamptz
WHERE c.city ILIKE '%Київ%'
  AND v.title ILIKE '%Engineer%'
  AND v.is_remote = TRUE
GROUP BY c.company_id, c.company_name, c.city
HAVING COUNT(a.application_id) >= 1
   AND AVG(v.salary) BETWEEN 20000 AND 180000
ORDER BY total_applications DESC, avg_salary DESC
LIMIT 50;
