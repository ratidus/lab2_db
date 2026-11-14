## Мета роботи

Набуття практичних навичок розроблення прикладного застосунку, що взаємодіє з реляційною базою даних PostgreSQL засобами параметризованих SQL-запитів (`%s`), підтримує пакетну генерацію 100 000+ псевдовипадкових записів засобами SQL, виконує багатотабличні пошукові запити з вимірюванням часу (мс) та коректно обробляє помилки обмежень цілісності.

## Опис предметної області та структури бази даних

База даних `lab1` перебуває у 3НФ і містить 5 таблиць:
- **`companies`** (`company_id` PK, `company_name`, `city`, `contact_email` UNIQUE) — компанії-роботодавці.
- **`candidates`** (`candidate_id` PK, `full_name`, `email` UNIQUE, `phone` UNIQUE) — кандидати.
- **`vacancies`** (`vacancy_id` PK, `company_id` FK &rarr; `companies` `ON DELETE RESTRICT`, `title`, `salary` `CHECK > 0`, `description`, `is_remote` BOOLEAN) — відкриті вакансії.
- **`resumes`** (`resume_id` PK, `candidate_id` FK &rarr; `candidates` `ON DELETE RESTRICT`, `title`, `skills`, `expected_salary` `CHECK > 0`) — резюме кандидатів.
- **`applications`** (`application_id` PK, `resume_id` FK &rarr; `resumes` `ON DELETE CASCADE`, `vacancy_id` FK &rarr; `vacancies` `ON DELETE CASCADE`, `apply_date`, `status` `CHECK`, `UNIQUE(resume_id, vacancy_id)`) — відгуки резюме на вакансії.

## Структура проєкту (MVC)

Усі файли розміщені безпосередньо в корені репозиторію за зразком:

```text
├── README.md                        # Опис проєкту та інструкція запуску
├── .env.example                     # Приклад конфігурації підключення до PostgreSQL
├── requirements.txt                 # Залежності (psycopg[binary], python-dotenv)
├── main.py                          # Точка входу (запуск Controller)
├── controller.py                    # Controller: обробка меню та координація між Model і View
├── model.py                         # Model: підключення до PostgreSQL, CRUD, генерація та пошук
├── view.py                          # View: консольне меню, введення даних та табличний вивід
└── queries.sql                      # SQL-скрипти створення таблиць, генерації та пошуку
```

- **`model.py` (`class Model`)** — встановлює з'єднання з PostgreSQL, автоматично створює/оновлює таблиці (`create_tables()`), виконує параметризовані CRUD-запити, SQL-генерацію тестових даних і 3 пошукові запити з вимірюванням часу (`time.perf_counter()`), перехоплюючи помилки `psycopg.errors` (`UniqueViolation`, `ForeignKeyViolation`, `CheckViolation`).
- **`view.py` (`class View`)** — виводить таблиці й повідомлення у консоль та зчитує вхідні параметри від користувача.
- **`controller.py` (`class Controller`)** — поєднує `Model` та `View`, реалізуючи цикл головного меню.
- **`main.py`** — створює екземпляр `Controller()` та запускає `controller.run()`.

## Встановлення та запуск

### Крок 1: Встановіть залежності

```bash
pip install -r requirements.txt
```

### Крок 2: Налаштуйте підключення до бази даних

Скопіюйте `.env.example` у `.env` та вкажіть пароль до вашого локального сервера PostgreSQL (або відредагуйте параметри за замовчуванням у `model.py`):

```ini
DB_NAME=lab1
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

### Крок 3: Запустіть застосунок

```bash
python main.py
```

## Меню користувача

- **`1–5`** — робота з таблицями `companies`, `candidates`, `vacancies`, `resumes`, `applications` (`1` — перегляд, `2` — додавання, `3` — редагування за ID, `4` — видалення за ID).
- **`6`** — пакетна генерація випадкових даних засобами SQL (`generate_series`, `random()`) із введенням кількості записів (зокрема **100 000 записів**).
- **`7`** — виконання 3 параметризованих пошукових запитів між декількома таблицями з виведенням часу виконання у мілісекундах.
- **`0`** — вихід із програми.
