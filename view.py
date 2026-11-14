class View:
    def show_message(self, message):
        print(message)

    def show_rows(self, columns, rows, elapsed_ms=None):
        if elapsed_ms is not None:
            print(f"\nЧас виконання запиту: {elapsed_ms:.2f} мс | Знайдено записів: {len(rows)}")
        if not rows:
            print("Записів не знайдено.")
            return

        col_widths = [len(str(col)) for col in columns]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], min(len(str(val)), 45))

        sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
        header = "| " + " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(columns)) + " |"

        print(sep)
        print(header)
        print(sep)
        for row in rows:
            line = "| " + " | ".join(
                (str(val)[:42] + "..." if len(str(val)) > 45 else str(val)).ljust(col_widths[i])
                for i, val in enumerate(row)
            ) + " |"
            print(line)
        print(sep)

    def get_int(self, prompt, default=None):
        while True:
            raw = input(prompt).strip()
            if not raw and default is not None:
                return default
            try:
                return int(raw)
            except ValueError:
                print("Помилка: введіть ціле число.")

    def get_float(self, prompt, default=None):
        while True:
            raw = input(prompt).strip()
            if not raw and default is not None:
                return default
            try:
                return float(raw.replace(",", "."))
            except ValueError:
                print("Помилка: введіть числове значення (наприклад, 45000).")

    def get_bool(self, prompt, default=True):
        while True:
            raw = input(f"{prompt} (True/False) [за замовч. {default}]: ").strip().lower()
            if not raw:
                return default
            if raw in ("true", "t", "1", "yes", "так"):
                return True
            if raw in ("false", "f", "0", "no", "ні"):
                return False
            print("Помилка: введіть True або False.")

    def get_str(self, prompt, default=None):
        while True:
            raw = input(prompt).strip()
            if not raw and default is not None:
                return default
            if raw:
                return raw
            print("Помилка: поле не може бути порожнім.")

    def get_id(self, entity_name):
        return self.get_int(f"Введіть ID ({entity_name}): ")

    # --- Введення даних для 5 таблиць ---
    def get_company_input(self):
        name = self.get_str("Введіть назву компанії: ")
        city = self.get_str("Введіть місто: ")
        email = self.get_str("Введіть контактний email: ")
        return name, city, email

    def get_candidate_input(self):
        full_name = self.get_str("Введіть ПІБ кандидата: ")
        email = self.get_str("Введіть email кандидата: ")
        phone = self.get_str("Введіть телефон кандидата (+380...): ")
        return full_name, email, phone

    def get_vacancy_input(self):
        company_id = self.get_int("Введіть ID компанії (company_id): ")
        title = self.get_str("Введіть назву посади: ")
        salary = self.get_float("Введіть зарплату (> 0): ")
        description = self.get_str("Введіть опис вакансії: ")
        is_remote = self.get_bool("Дистанційна робота (is_remote)?", default=True)
        return company_id, title, salary, description, is_remote

    def get_resume_input(self):
        candidate_id = self.get_int("Введіть ID кандидата (candidate_id): ")
        title = self.get_str("Введіть заголовок резюме: ")
        skills = self.get_str("Введіть перелік навичок: ")
        expected_salary = self.get_float("Введіть очікувану зарплату (> 0): ")
        return candidate_id, title, skills, expected_salary

    def get_application_input(self):
        resume_id = self.get_int("Введіть ID резюме (resume_id): ")
        vacancy_id = self.get_int("Введіть ID вакансії (vacancy_id): ")
        status = self.get_str(
            "Введіть статус (Submitted / Interview / Offer / Rejected) [Submitted]: ",
            default="Submitted",
        )
        return resume_id, vacancy_id, status

    # --- Введення параметрів для 3 пошукових запитів ---
    def get_search_1_input(self):
        print("\n--- Пошук №1: Вакансії та компанії (2 таблиці) ---")
        min_salary = self.get_float("Мінімальна зарплата [30000]: ", default=30000.0)
        max_salary = self.get_float("Максимальна зарплата [120000]: ", default=120000.0)
        title_like = self.get_str("Шаблон назви посади LIKE [%Engineer%]: ", default="%Engineer%")
        city_like = self.get_str("Шаблон міста LIKE [%Київ%]: ", default="%Київ%")
        is_remote = self.get_bool("Дистанційна робота (is_remote)", default=True)
        return min_salary, max_salary, title_like, city_like, is_remote

    def get_search_2_input(self):
        print("\n--- Пошук №2: Відгуки кандидатів на вакансії (5 таблиць) ---")
        date_from = self.get_str("Дата подання ВІД (YYYY-MM-DD) [2025-01-01]: ", default="2025-01-01")
        date_to = self.get_str("Дата подання ДО (YYYY-MM-DD) [2026-12-31]: ", default="2026-12-31")
        min_exp = self.get_float("Мін. очікувана зарплата [25000]: ", default=25000.0)
        max_exp = self.get_float("Макс. очікувана зарплата [110000]: ", default=110000.0)
        skills_like = self.get_str("Шаблон навичок у резюме LIKE [%PostgreSQL%]: ", default="%PostgreSQL%")
        status_like = self.get_str("Шаблон статусу LIKE [Interview%]: ", default="Interview%")
        is_remote = self.get_bool("Дистанційна вакансія (is_remote)", default=True)
        return date_from, date_to, min_exp, max_exp, skills_like, status_like, is_remote

    def get_search_3_input(self):
        print("\n--- Пошук №3: Статистика по компаніях з GROUP BY та HAVING (3 таблиці) ---")
        city_like = self.get_str("Шаблон міста LIKE [%Київ%]: ", default="%Київ%")
        title_like = self.get_str("Шаблон посади LIKE [%Engineer%]: ", default="%Engineer%")
        is_remote = self.get_bool("Дистанційні вакансії (is_remote)", default=True)
        date_from = self.get_str("Дата відгуків ВІД (YYYY-MM-DD) [2025-01-01]: ", default="2025-01-01")
        date_to = self.get_str("Дата відгуків ДО (YYYY-MM-DD) [2026-12-31]: ", default="2026-12-31")
        min_apps = self.get_int("Мін. кількість відгуків у HAVING [1]: ", default=1)
        min_avg = self.get_float("Мін. середня зарплата компанії у HAVING [20000]: ", default=20000.0)
        max_avg = self.get_float("Макс. середня зарплата компанії у HAVING [180000]: ", default=180000.0)
        return city_like, title_like, is_remote, date_from, date_to, min_apps, min_avg, max_avg
