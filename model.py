import os
import sys
import time
from pathlib import Path
import psycopg
from psycopg import errors

try:
    from dotenv import load_dotenv
    base_dir = Path(__file__).resolve().parent
    if (base_dir / ".env").exists():
        load_dotenv(base_dir / ".env")
    elif (base_dir / ".env.example").exists():
        load_dotenv(base_dir / ".env.example")
except ImportError:
    pass


class Model:
    def __init__(self):
        dbname = os.getenv("DB_NAME", "lab1")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")

        try:
            self.conn = psycopg.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
            )
            self.create_tables()
        except psycopg.OperationalError:
            print(
                f"\n[ПОМИЛКА ПІДКЛЮЧЕННЯ ДО БД] Не вдалося підключитися до PostgreSQL "
                f"(host={host}, port={port}, dbname={dbname}, user={user}).\n"
                "Перевірте пароль та порт у model.py або .env."
            )
            sys.exit(1)

    def create_tables(self):
        with self.conn.cursor() as c:
            c.execute("""
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

                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    -- 1. Перевірка обмежень CHECK
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_vacancies_salary_positive') THEN
                        ALTER TABLE public.vacancies
                            ADD CONSTRAINT chk_vacancies_salary_positive CHECK (salary IS NULL OR salary > 0);
                    END IF;

                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_resumes_expected_salary_positive') THEN
                        ALTER TABLE public.resumes
                            ADD CONSTRAINT chk_resumes_expected_salary_positive CHECK (expected_salary IS NULL OR expected_salary > 0);
                    END IF;

                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_applications_status') THEN
                        ALTER TABLE public.applications
                            ADD CONSTRAINT chk_applications_status CHECK (status IN ('Submitted', 'Interview', 'Offer', 'Rejected'));
                    END IF;

                    -- 1.1. Гарантування UNIQUE (resume_id, vacancy_id) у таблиці applications
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint
                        WHERE conrelid = 'public.applications'::regclass AND contype = 'u'
                    ) THEN
                        DELETE FROM public.applications a USING public.applications b
                        WHERE a.application_id > b.application_id
                          AND a.resume_id = b.resume_id
                          AND a.vacancy_id = b.vacancy_id;

                        ALTER TABLE public.applications
                            ADD CONSTRAINT applications_resume_id_vacancy_id_key UNIQUE (resume_id, vacancy_id);
                    END IF;

                    -- 2. Гарантування ON DELETE RESTRICT для vacancies -> companies
                    FOR r IN (
                        SELECT conname FROM pg_constraint
                        WHERE conrelid = 'public.vacancies'::regclass AND contype = 'f'
                    ) LOOP
                        EXECUTE 'ALTER TABLE public.vacancies DROP CONSTRAINT ' || quote_ident(r.conname);
                    END LOOP;

                    ALTER TABLE public.vacancies
                        ADD CONSTRAINT vacancies_company_id_fkey
                        FOREIGN KEY (company_id) REFERENCES public.companies(company_id)
                        ON DELETE RESTRICT ON UPDATE CASCADE;

                    -- 3. Гарантування ON DELETE RESTRICT для resumes -> candidates
                    FOR r IN (
                        SELECT conname FROM pg_constraint
                        WHERE conrelid = 'public.resumes'::regclass AND contype = 'f'
                    ) LOOP
                        EXECUTE 'ALTER TABLE public.resumes DROP CONSTRAINT ' || quote_ident(r.conname);
                    END LOOP;

                    ALTER TABLE public.resumes
                        ADD CONSTRAINT resumes_candidate_id_fkey
                        FOREIGN KEY (candidate_id) REFERENCES public.candidates(candidate_id)
                        ON DELETE RESTRICT ON UPDATE CASCADE;

                    -- 4. Гарантування ON DELETE CASCADE для applications -> resumes, vacancies
                    FOR r IN (
                        SELECT conname FROM pg_constraint
                        WHERE conrelid = 'public.applications'::regclass AND contype = 'f'
                    ) LOOP
                        EXECUTE 'ALTER TABLE public.applications DROP CONSTRAINT ' || quote_ident(r.conname);
                    END LOOP;

                    ALTER TABLE public.applications
                        ADD CONSTRAINT applications_resume_id_fkey
                        FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id)
                        ON DELETE CASCADE ON UPDATE CASCADE;

                    ALTER TABLE public.applications
                        ADD CONSTRAINT applications_vacancy_id_fkey
                        FOREIGN KEY (vacancy_id) REFERENCES public.vacancies(vacancy_id)
                        ON DELETE CASCADE ON UPDATE CASCADE;
                END $$;

                -- 5. Відновлення базових даних з ЛР №1 (якщо company_id=1 було видалено під час тесту)
                UPDATE public.companies SET company_id = 1
                WHERE contact_email = 'hr@ajax.com' AND company_id <> 1
                  AND NOT EXISTS (SELECT 1 FROM public.companies WHERE company_id = 1);

                INSERT INTO public.companies (company_id, company_name, city, contact_email)
                VALUES
                    (1, 'Ajax', 'Київ', 'hr@ajax.com'),
                    (2, 'EPAM Systems', 'Львів', 'talent@epam.com'),
                    (3, 'Genesis', 'Київ', 'careers@gen.tech'),
                    (4, 'Grammarly', 'Київ', 'jobs@grammarly.com')
                ON CONFLICT DO NOTHING;

                INSERT INTO public.candidates (candidate_id, full_name, email, phone)
                VALUES
                    (1, 'Кученьов Ілля', 'kuchenov.ilya@gmail.com', '+380671112233'),
                    (2, 'Олександр Мельник', 'o.melnyk@ukr.net', '+380504445566'),
                    (3, 'Марія Коваленко', 'mariya.kovalenko@gmail.com', '+380937778899'),
                    (4, 'Дмитро Шевченко', 'dmitriy.shev@meta.ua', '+380682223344')
                ON CONFLICT DO NOTHING;

                INSERT INTO public.vacancies (vacancy_id, company_id, title, salary, description, is_remote)
                VALUES
                    (1, 1, 'Junior Golang Developer', 35000.00, 'Розробка мікросервісів, знання PostgreSQL та Docker обов''язкове.', false),
                    (2, 2, 'Middle Python Engineer', 85000.00, 'Розробка бекенду на Django/FastAPI, проєктування реляційних баз даних.', true),
                    (3, 3, 'Data Analyst', 50000.00, 'Складання SQL-запитів, робота з BI-системами та аналітика метрик.', true),
                    (4, 4, 'DevOps Engineer', 110000.00, 'Налаштування CI/CD pipelines, робота з Kubernetes та хмарною інфраструктурою.', false)
                ON CONFLICT DO NOTHING;

                INSERT INTO public.resumes (resume_id, candidate_id, title, skills, expected_salary)
                VALUES
                    (1, 1, 'Golang & Backend Developer', 'Golang, PostgreSQL, Docker, Git, REST API', 40000.00),
                    (2, 2, 'Python / Backend Developer', 'Python, FastAPI, PostgreSQL, Redis, SQLAlchemy', 80000.00),
                    (3, 3, 'Junior Data Analyst', 'SQL, Python, Pandas, PowerBI, Excel', 45000.00),
                    (4, 4, 'Cloud & DevOps Specialist', 'Linux, Docker, Kubernetes, Terraform, AWS', 100000.00)
                ON CONFLICT DO NOTHING;

                INSERT INTO public.applications (application_id, resume_id, vacancy_id, apply_date, status)
                VALUES
                    (1, 1, 1, '2026-10-01 10:30:00+03', 'Interview'),
                    (2, 2, 2, '2026-10-02 12:15:00+03', 'Submitted'),
                    (3, 3, 3, '2026-10-03 14:00:00+03', 'Offer'),
                    (4, 1, 2, '2026-10-04 16:45:00+03', 'Submitted'),
                    (5, 4, 4, '2026-10-05 09:20:00+03', 'Rejected')
                ON CONFLICT DO NOTHING;

                -- Синхронізація лічильників SERIAL
                SELECT setval(pg_get_serial_sequence('public.companies', 'company_id'), COALESCE((SELECT MAX(company_id) FROM public.companies), 1));
                SELECT setval(pg_get_serial_sequence('public.candidates', 'candidate_id'), COALESCE((SELECT MAX(candidate_id) FROM public.candidates), 1));
                SELECT setval(pg_get_serial_sequence('public.vacancies', 'vacancy_id'), COALESCE((SELECT MAX(vacancy_id) FROM public.vacancies), 1));
                SELECT setval(pg_get_serial_sequence('public.resumes', 'resume_id'), COALESCE((SELECT MAX(resume_id) FROM public.resumes), 1));
                SELECT setval(pg_get_serial_sequence('public.applications', 'application_id'), COALESCE((SELECT MAX(application_id) FROM public.applications), 1));
            """)
        self.conn.commit()

    def reset_generated_data(self):
        """Очищає всі раніше згенеровані тестові записи, залишаючи тільки початкові рядки з ЛР №1."""
        sql = """
            DELETE FROM public.applications WHERE application_id > 5;
            DELETE FROM public.vacancies WHERE vacancy_id > 5;
            DELETE FROM public.resumes WHERE resume_id > 4;
            DELETE FROM public.candidates WHERE candidate_id > 4;
            DELETE FROM public.companies WHERE company_id > 4;

            SELECT setval(pg_get_serial_sequence('public.companies', 'company_id'), COALESCE((SELECT MAX(company_id) FROM public.companies), 1));
            SELECT setval(pg_get_serial_sequence('public.candidates', 'candidate_id'), COALESCE((SELECT MAX(candidate_id) FROM public.candidates), 1));
            SELECT setval(pg_get_serial_sequence('public.vacancies', 'vacancy_id'), COALESCE((SELECT MAX(vacancy_id) FROM public.vacancies), 1));
            SELECT setval(pg_get_serial_sequence('public.resumes', 'resume_id'), COALESCE((SELECT MAX(resume_id) FROM public.resumes), 1));
            SELECT setval(pg_get_serial_sequence('public.applications', 'application_id'), COALESCE((SELECT MAX(application_id) FROM public.applications), 1));
        """
        start_time = time.perf_counter()
        try:
            with self.conn.cursor() as c:
                c.execute(sql)
            self.conn.commit()
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return True, f"Попередні згенеровані записи очищено за {elapsed_ms:.2f} мс (залишено початкові дані ЛР №1)."
        except psycopg.Error as err:
            return False, self._explain_error(err)

    def _explain_error(self, err):
        self.conn.rollback()
        if isinstance(err, errors.UniqueViolation):
            return "Помилка унікальності (UNIQUE): запис із таким email, телефоном або парою (resume_id, vacancy_id) вже існує."
        if isinstance(err, errors.ForeignKeyViolation):
            return (
                "Помилка зовнішнього ключа (FOREIGN KEY): вказаний ID пов'язаного запису не існує "
                "або видалення заборонено правилом ON DELETE RESTRICT (є залежні записи)."
            )
        if isinstance(err, errors.CheckViolation):
            return (
                "Помилка перевірки обмеження (CHECK): зарплата має бути > 0, "
                "а статус — одним зі значень: Submitted, Interview, Offer, Rejected."
            )
        if isinstance(err, errors.NotNullViolation):
            return "Помилка NOT NULL: обов'язкове поле не може бути порожнім."
        if isinstance(err, errors.DataError):
            return "Помилка формату даних: введене значення не відповідає типу стовпця або перевищує довжину."
        return "Операцію відхилено базою даних через порушення обмежень."

    def execute_change(self, sql, params=None):
        start_time = time.perf_counter()
        try:
            with self.conn.cursor() as c:
                c.execute(sql, params)
                affected = c.rowcount
            self.conn.commit()
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            if affected == 0:
                return False, f"Запис із вказаним ID не знайдено або дані вже існують (змінено рядків: 0, час: {elapsed_ms:.2f} мс)."
            return True, f"Операцію виконано успішно за {elapsed_ms:.2f} мс (змінено рядків: {affected})."
        except psycopg.Error as err:
            return False, self._explain_error(err)

    def execute_select(self, sql, params=None):
        start_time = time.perf_counter()
        try:
            with self.conn.cursor() as c:
                c.execute(sql, params)
                rows = c.fetchall()
                columns = [desc[0] for desc in c.description] if c.description else []
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return True, columns, rows, elapsed_ms, None
        except psycopg.Error as err:
            return False, [], [], 0.0, self._explain_error(err)

    # --- 1. Таблиця companies ---
    def get_companies(self, limit=20):
        return self.execute_select(
            "SELECT company_id, company_name, city, contact_email FROM public.companies ORDER BY company_id LIMIT %s",
            (limit,),
        )

    def add_company(self, name, city, email):
        return self.execute_change(
            "INSERT INTO public.companies (company_name, city, contact_email) VALUES (%s, %s, %s)",
            (name, city, email),
        )

    def update_company(self, company_id, name, city, email):
        return self.execute_change(
            "UPDATE public.companies SET company_name=%s, city=%s, contact_email=%s WHERE company_id=%s",
            (name, city, email, company_id),
        )

    def delete_company(self, company_id):
        return self.execute_change("DELETE FROM public.companies WHERE company_id=%s", (company_id,))

    # --- 2. Таблиця candidates ---
    def get_candidates(self, limit=20):
        return self.execute_select(
            "SELECT candidate_id, full_name, email, phone FROM public.candidates ORDER BY candidate_id LIMIT %s",
            (limit,),
        )

    def add_candidate(self, full_name, email, phone):
        return self.execute_change(
            "INSERT INTO public.candidates (full_name, email, phone) VALUES (%s, %s, %s)",
            (full_name, email, phone),
        )

    def update_candidate(self, candidate_id, full_name, email, phone):
        return self.execute_change(
            "UPDATE public.candidates SET full_name=%s, email=%s, phone=%s WHERE candidate_id=%s",
            (full_name, email, phone, candidate_id),
        )

    def delete_candidate(self, candidate_id):
        return self.execute_change("DELETE FROM public.candidates WHERE candidate_id=%s", (candidate_id,))

    # --- 3. Таблиця vacancies ---
    def get_vacancies(self, limit=20):
        return self.execute_select(
            """
            SELECT v.vacancy_id, v.company_id, c.company_name, v.title, v.salary, v.is_remote
            FROM public.vacancies v
            JOIN public.companies c ON v.company_id = c.company_id
            ORDER BY v.vacancy_id LIMIT %s
            """,
            (limit,),
        )

    def add_vacancy(self, company_id, title, salary, description, is_remote):
        return self.execute_change(
            "INSERT INTO public.vacancies (company_id, title, salary, description, is_remote) VALUES (%s, %s, %s, %s, %s)",
            (company_id, title, salary, description, is_remote),
        )

    def update_vacancy(self, vacancy_id, company_id, title, salary, description, is_remote):
        return self.execute_change(
            """
            UPDATE public.vacancies
            SET company_id=%s, title=%s, salary=%s, description=%s, is_remote=%s
            WHERE vacancy_id=%s
            """,
            (company_id, title, salary, description, is_remote, vacancy_id),
        )

    def delete_vacancy(self, vacancy_id):
        ok_cnt, _, rows_cnt, _, _ = self.execute_select(
            "SELECT COUNT(*) FROM public.applications WHERE vacancy_id=%s", (vacancy_id,)
        )
        cascaded = rows_cnt[0][0] if ok_cnt and rows_cnt else 0
        ok, msg = self.execute_change("DELETE FROM public.vacancies WHERE vacancy_id=%s", (vacancy_id,))
        if ok:
            msg += f" Каскадно видалено пов'язаних відгуків (ON DELETE CASCADE): {cascaded}."
        return ok, msg

    # --- 4. Таблиця resumes ---
    def get_resumes(self, limit=20):
        return self.execute_select(
            """
            SELECT r.resume_id, r.candidate_id, c.full_name, r.title, r.expected_salary, r.skills
            FROM public.resumes r
            JOIN public.candidates c ON r.candidate_id = c.candidate_id
            ORDER BY r.resume_id LIMIT %s
            """,
            (limit,),
        )

    def add_resume(self, candidate_id, title, skills, expected_salary):
        return self.execute_change(
            "INSERT INTO public.resumes (candidate_id, title, skills, expected_salary) VALUES (%s, %s, %s, %s)",
            (candidate_id, title, skills, expected_salary),
        )

    def update_resume(self, resume_id, candidate_id, title, skills, expected_salary):
        return self.execute_change(
            """
            UPDATE public.resumes
            SET candidate_id=%s, title=%s, skills=%s, expected_salary=%s
            WHERE resume_id=%s
            """,
            (candidate_id, title, skills, expected_salary, resume_id),
        )

    def delete_resume(self, resume_id):
        ok_cnt, _, rows_cnt, _, _ = self.execute_select(
            "SELECT COUNT(*) FROM public.applications WHERE resume_id=%s", (resume_id,)
        )
        cascaded = rows_cnt[0][0] if ok_cnt and rows_cnt else 0
        ok, msg = self.execute_change("DELETE FROM public.resumes WHERE resume_id=%s", (resume_id,))
        if ok:
            msg += f" Каскадно видалено пов'язаних відгуків (ON DELETE CASCADE): {cascaded}."
        return ok, msg

    # --- 5. Таблиця applications ---
    def get_applications(self, limit=20):
        return self.execute_select(
            """
            SELECT a.application_id, a.resume_id, a.vacancy_id,
                   to_char(a.apply_date, 'YYYY-MM-DD HH24:MI') AS apply_date, a.status
            FROM public.applications a
            ORDER BY a.application_id LIMIT %s
            """,
            (limit,),
        )

    def add_application(self, resume_id, vacancy_id, status):
        return self.execute_change(
            "INSERT INTO public.applications (resume_id, vacancy_id, status) VALUES (%s, %s, %s)",
            (resume_id, vacancy_id, status),
        )

    def update_application(self, application_id, status):
        return self.execute_change(
            "UPDATE public.applications SET status=%s WHERE application_id=%s",
            (status, application_id),
        )

    def delete_application(self, application_id):
        return self.execute_change("DELETE FROM public.applications WHERE application_id=%s", (application_id,))

    # --- Пакетна генерація даних засобами SQL ---
    def generate_companies(self, count):
        sql = """
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
            FROM generate_series(1, %s) AS gs CROSS JOIN base;
        """
        return self.execute_change(sql, (count,))

    def generate_candidates(self, count):
        sql = """
            WITH base AS (SELECT COALESCE(MAX(candidate_id), 0) AS max_id FROM public.candidates)
            INSERT INTO public.candidates (full_name, email, phone)
            SELECT
                (ARRAY['Олександр', 'Ілля', 'Дмитро', 'Максим', 'Артем', 'Марія', 'Анна', 'Софія'])[1 + trunc(random() * 8)::int]
                || ' ' ||
                (ARRAY['Мельник', 'Шевченко', 'Коваленко', 'Бондаренко', 'Бойко', 'Ткаченко', 'Кравченко', 'Коваль'])[1 + trunc(random() * 8)::int],
                'cand.' || lower(chr(trunc(65 + random() * 25)::int) || chr(trunc(65 + random() * 25)::int))
                || '.' || (base.max_id + gs)::text || '@gmail.com',
                '+380' || lpad((500000000 + base.max_id + gs)::text, 9, '0')
            FROM generate_series(1, %s) AS gs CROSS JOIN base;
        """
        return self.execute_change(sql, (count,))

    def generate_vacancies(self, count):
        sql = """
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
            FROM generate_series(1, %s) AS gs CROSS JOIN comp
            WHERE comp.cnt > 0;
        """
        return self.execute_change(sql, (count,))

    def generate_resumes(self, count):
        sql = """
            WITH cand AS (SELECT array_agg(candidate_id) AS ids, count(*)::int AS cnt FROM public.candidates)
            INSERT INTO public.resumes (candidate_id, title, skills, expected_salary)
            SELECT
                cand.ids[1 + trunc(random() * cand.cnt)::int],
                (ARRAY['Python / Backend Developer', 'Golang Developer', 'Computer Vision Engineer', 'Data Analyst', 'DevOps Engineer'])[1 + trunc(random() * 5)::int],
                (ARRAY['Python, PostgreSQL, Docker, Git', 'Golang, PostgreSQL, Redis, gRPC', 'C++, Python, OpenCV, PyTorch, SQL', 'SQL, Python, Pandas, PowerBI'])[1 + trunc(random() * 4)::int],
                round((18000 + random() * 142000)::numeric, 2)
            FROM generate_series(1, %s) AS gs CROSS JOIN cand
            WHERE cand.cnt > 0;
        """
        return self.execute_change(sql, (count,))

    def generate_applications(self, count):
        sql = """
            WITH r_pool AS (SELECT array_agg(resume_id ORDER BY resume_id) AS ids, count(*)::bigint AS cnt FROM public.resumes),
                 v_pool AS (SELECT array_agg(vacancy_id ORDER BY vacancy_id) AS ids, count(*)::bigint AS cnt FROM public.vacancies),
                 offset_base AS (SELECT COUNT(*)::bigint AS off FROM public.applications)
            INSERT INTO public.applications (resume_id, vacancy_id, apply_date, status)
            SELECT
                r_pool.ids[1 + (((gs + offset_base.off - 1) / v_pool.cnt) %% r_pool.cnt)::int],
                v_pool.ids[1 + ((gs + offset_base.off - 1) %% v_pool.cnt)::int],
                timestamptz '2025-01-01 08:00:00+02' +
                    random() * (timestamptz '2026-11-14 20:00:00+02' - timestamptz '2025-01-01 08:00:00+02'),
                (ARRAY['Submitted', 'Interview', 'Offer', 'Rejected'])[1 + trunc(random() * 4)::int]
            FROM generate_series(1, %s) AS gs
            CROSS JOIN r_pool
            CROSS JOIN v_pool
            CROSS JOIN offset_base
            WHERE r_pool.cnt > 0 AND v_pool.cnt > 0
            ON CONFLICT DO NOTHING;
        """
        return self.execute_change(sql, (count,))

    # --- 3 параметризовані пошукові запити ---
    def search_vacancies(self, min_salary, max_salary, title_like, city_like, is_remote):
        sql = """
            SELECT v.vacancy_id, c.company_name, c.city, v.title, v.salary, v.is_remote, c.contact_email
            FROM public.vacancies v
            JOIN public.companies c ON v.company_id = c.company_id
            WHERE v.salary BETWEEN %s AND %s
              AND v.title ILIKE %s
              AND c.city ILIKE %s
              AND v.is_remote = %s
            ORDER BY v.salary DESC
            LIMIT 20;
        """
        return self.execute_select(sql, (min_salary, max_salary, title_like, city_like, is_remote))

    def search_applications(self, date_from, date_to, min_exp, max_exp, skills_like, status_like, is_remote):
        sql = """
            SELECT a.application_id, cand.full_name, r.title AS resume_title, r.expected_salary,
                   comp.company_name, v.title AS vacancy_title,
                   to_char(a.apply_date, 'YYYY-MM-DD HH24:MI') AS apply_date, a.status
            FROM public.applications a
            JOIN public.resumes r       ON a.resume_id = r.resume_id
            JOIN public.candidates cand ON r.candidate_id = cand.candidate_id
            JOIN public.vacancies v     ON a.vacancy_id = v.vacancy_id
            JOIN public.companies comp  ON v.company_id = comp.company_id
            WHERE a.apply_date BETWEEN %s::timestamptz AND %s::timestamptz
              AND r.expected_salary BETWEEN %s AND %s
              AND r.skills ILIKE %s
              AND a.status LIKE %s
              AND v.is_remote = %s
            ORDER BY a.apply_date DESC
            LIMIT 20;
        """
        return self.execute_select(
            sql, (date_from, date_to, min_exp, max_exp, skills_like, status_like, is_remote)
        )

    def search_company_stats(
        self, city_like, title_like, is_remote, date_from, date_to, min_apps, min_avg, max_avg
    ):
        sql = """
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
                  AND a.apply_date BETWEEN %s::timestamptz AND %s::timestamptz
            WHERE c.city ILIKE %s
              AND v.title ILIKE %s
              AND v.is_remote = %s
            GROUP BY c.company_id, c.company_name, c.city
            HAVING COUNT(a.application_id) >= %s
               AND AVG(v.salary) BETWEEN %s AND %s
            ORDER BY total_applications DESC, avg_salary DESC
            LIMIT 20;
        """
        return self.execute_select(
            sql, (date_from, date_to, city_like, title_like, is_remote, min_apps, min_avg, max_avg)
        )
