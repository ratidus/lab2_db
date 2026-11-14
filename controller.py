from model import Model
from view import View


class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()

    def run(self):
        while True:
            choice = self.show_menu()
            if choice == "1":
                self.companies_menu()
            elif choice == "2":
                self.candidates_menu()
            elif choice == "3":
                self.vacancies_menu()
            elif choice == "4":
                self.resumes_menu()
            elif choice == "5":
                self.applications_menu()
            elif choice == "6":
                self.generate_data_menu()
            elif choice == "7":
                self.search_menu()
            elif choice == "0":
                self.view.show_message("Роботу завершено.")
                break
            else:
                self.view.show_message("Невірний вибір, спробуйте ще раз.")

    def show_menu(self):
        self.view.show_message("\n=== ГОЛОВНЕ МЕНЮ (Платформа пошуку роботи) ===")
        self.view.show_message("1. Таблиця companies (Компанії)")
        self.view.show_message("2. Таблиця candidates (Кандидати)")
        self.view.show_message("3. Таблиця vacancies (Вакансії)")
        self.view.show_message("4. Таблиця resumes (Резюме)")
        self.view.show_message("5. Таблиця applications (Відгуки)")
        self.view.show_message("6. Генерація випадкових даних (SQL)")
        self.view.show_message("7. Пошукові запити (3 запити з фільтрами)")
        self.view.show_message("0. Вихід")
        return input("Оберіть пункт: ").strip()

    def show_crud_menu(self, title):
        self.view.show_message(f"\n--- {title} ---")
        self.view.show_message("1. Переглянути записи")
        self.view.show_message("2. Додати запис")
        self.view.show_message("3. Оновити запис")
        self.view.show_message("4. Видалити запис")
        self.view.show_message("0. Назад")
        return input("Ваш вибір: ").strip()

    def _display_select(self, result):
        ok, cols, rows, elapsed_ms, err = result
        if ok:
            self.view.show_rows(cols, rows, elapsed_ms)
        else:
            self.view.show_message(err)

    def _display_change(self, result):
        ok, msg = result
        self.view.show_message(msg)

    # --- 1. Компанії ---
    def companies_menu(self):
        choice = self.show_crud_menu("Компанії (companies)")
        if choice == "1":
            self._display_select(self.model.get_companies())
        elif choice == "2":
            name, city, email = self.view.get_company_input()
            self._display_change(self.model.add_company(name, city, email))
        elif choice == "3":
            cid = self.view.get_id("company_id")
            name, city, email = self.view.get_company_input()
            self._display_change(self.model.update_company(cid, name, city, email))
        elif choice == "4":
            cid = self.view.get_id("company_id")
            self._display_change(self.model.delete_company(cid))

    # --- 2. Кандидати ---
    def candidates_menu(self):
        choice = self.show_crud_menu("Кандидати (candidates)")
        if choice == "1":
            self._display_select(self.model.get_candidates())
        elif choice == "2":
            full_name, email, phone = self.view.get_candidate_input()
            self._display_change(self.model.add_candidate(full_name, email, phone))
        elif choice == "3":
            cand_id = self.view.get_id("candidate_id")
            full_name, email, phone = self.view.get_candidate_input()
            self._display_change(self.model.update_candidate(cand_id, full_name, email, phone))
        elif choice == "4":
            cand_id = self.view.get_id("candidate_id")
            self._display_change(self.model.delete_candidate(cand_id))

    # --- 3. Вакансії ---
    def vacancies_menu(self):
        choice = self.show_crud_menu("Вакансії (vacancies)")
        if choice == "1":
            self._display_select(self.model.get_vacancies())
        elif choice == "2":
            company_id, title, salary, desc, is_remote = self.view.get_vacancy_input()
            self._display_change(self.model.add_vacancy(company_id, title, salary, desc, is_remote))
        elif choice == "3":
            vid = self.view.get_id("vacancy_id")
            company_id, title, salary, desc, is_remote = self.view.get_vacancy_input()
            self._display_change(self.model.update_vacancy(vid, company_id, title, salary, desc, is_remote))
        elif choice == "4":
            vid = self.view.get_id("vacancy_id")
            self._display_change(self.model.delete_vacancy(vid))

    # --- 4. Резюме ---
    def resumes_menu(self):
        choice = self.show_crud_menu("Резюме (resumes)")
        if choice == "1":
            self._display_select(self.model.get_resumes())
        elif choice == "2":
            cand_id, title, skills, exp_sal = self.view.get_resume_input()
            self._display_change(self.model.add_resume(cand_id, title, skills, exp_sal))
        elif choice == "3":
            rid = self.view.get_id("resume_id")
            cand_id, title, skills, exp_sal = self.view.get_resume_input()
            self._display_change(self.model.update_resume(rid, cand_id, title, skills, exp_sal))
        elif choice == "4":
            rid = self.view.get_id("resume_id")
            self._display_change(self.model.delete_resume(rid))

    # --- 5. Відгуки ---
    def applications_menu(self):
        choice = self.show_crud_menu("Відгуки (applications)")
        if choice == "1":
            self._display_select(self.model.get_applications())
        elif choice == "2":
            rid, vid, status = self.view.get_application_input()
            self._display_change(self.model.add_application(rid, vid, status))
        elif choice == "3":
            aid = self.view.get_id("application_id")
            status = self.view.get_str("Новий статус (Submitted/Interview/Offer/Rejected): ")
            self._display_change(self.model.update_application(aid, status))
        elif choice == "4":
            aid = self.view.get_id("application_id")
            self._display_change(self.model.delete_application(aid))

    # --- 6. Генерація даних ---
    def generate_data_menu(self):
        self.view.show_message("\n--- Генерація випадкових даних засобами SQL ---")
        self.view.show_message("1. Згенерувати компанії (companies)")
        self.view.show_message("2. Згенерувати кандидатів (candidates)")
        self.view.show_message("3. Згенерувати вакансії (vacancies)")
        self.view.show_message("4. Згенерувати резюме (resumes)")
        self.view.show_message("5. Згенерувати відгуки (applications)")
        self.view.show_message("6. Згенерувати повний набір (включно зі 100 000 записів)")
        sub = input("Ваш вибір: ").strip()
        if sub in ("1", "2", "3", "4", "5", "6"):
            count = self.view.get_int("Введіть кількість записів для генерації [100000]: ", default=100000)
            if sub == "1":
                self._display_change(self.model.generate_companies(count))
            elif sub == "2":
                self._display_change(self.model.generate_candidates(count))
            elif sub == "3":
                self._display_change(self.model.generate_vacancies(count))
            elif sub == "4":
                self._display_change(self.model.generate_resumes(count))
            elif sub == "5":
                self._display_change(self.model.generate_applications(count))
            elif sub == "6":
                self._display_change(self.model.generate_companies(max(1000, count // 100)))
                self._display_change(self.model.generate_candidates(max(5000, count // 20)))
                self._display_change(self.model.generate_vacancies(count))
                self._display_change(self.model.generate_resumes(max(10000, count // 10)))
                self._display_change(self.model.generate_applications(count))

    # --- 7. Пошук ---
    def search_menu(self):
        self.view.show_message("\n--- Пошукові запити ---")
        self.view.show_message("1. Пошук вакансій за зарплатою, назвою, містом і форматом (2 таблиці)")
        self.view.show_message("2. Пошук відгуків за датами, очікуваною зарплатою, навичками і статусом (5 таблиць)")
        self.view.show_message("3. Статистика компаній з агрегуванням GROUP BY та HAVING (3 таблиці)")
        sub = input("Ваш вибір: ").strip()
        if sub == "1":
            params = self.view.get_search_1_input()
            self._display_select(self.model.search_vacancies(*params))
        elif sub == "2":
            params = self.view.get_search_2_input()
            self._display_select(self.model.search_applications(*params))
        elif sub == "3":
            params = self.view.get_search_3_input()
            self._display_select(self.model.search_company_stats(*params))
