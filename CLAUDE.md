# CLAUDE.md - Guidance for AI Assistants (Real Estate Deal Finder)

## 1. Project Overview & Goal

* **Project Name:** `Real Estate Deal Finder`
* **Description:** A Python application to find cash-flowing rental properties (1-4 units) in specified US ZIP codes by fetching data from Zillow (via RapidAPI) and RentCast APIs, applying financial calculations, and filtering based on user-defined criteria (CoC return, cash flow). This is an internal tool for a newsletter author.
* **Primary Goal:** To provide a simple, efficient way to shortlist investable rental properties based on Zillow listings and RentCast rent estimates, outputting results to a CSV file.

## 2. Technology Stack

* **Primary Language:** Python (Version 3.9+ preferred)
* **Package Manager:** pip
* **Key Libraries:**
    * `requests` (for API calls)
    * `python-dotenv` (for environment variables)
    * `APScheduler` (for potential future scheduling, or simple time-based caching logic)
    * `pytest` (for testing)
    * `pandas` (Optional, consider for data manipulation/CSV export if beneficial)
    * `logging` (standard library)
* **APIs Used:** Zillow (via RapidAPI), RentCast

## 3. Development Workflow & Commands

* **Setup Virtual Environment:** `python -m venv venv` then `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
* **Install Dependencies:** `pip install -r requirements.txt` (and `pip install -r requirements-dev.txt` if created)
* **Run Locally:** `python src/real_estate_deal_finder/main.py` (or the designated entry point script)
* **Run Linters/Formatters:** `black .`, `ruff check .` (or `flake8`) - *Assuming Black/Ruff are used*
* **Run All Tests:** `pytest`
* **Run Specific Test File:** `pytest tests/test_calculations.py`
* **Run Specific Test Case:** `pytest tests/test_calculations.py -k "test_specific_scenario"`
* **Test Framework:** `pytest`
* **Test File Location:** `tests/` directory, files named `test_*.py`.

## 4. Code Style & Structure Guidelines

* **Language:** Use Python 3.9+ features and type hints consistently (`typing` module). Check types with MyPy if configured.
* **Linter/Formatter:** Use Black for formatting and Ruff/Flake8 for linting (check `pyproject.toml` or relevant config files). Strictly adhere to PEP 8.
* **Imports:** Group imports: 1. Standard library, 2. Third-party libraries, 3. Internal project modules (`src.real_estate_deal_finder...`). Separate groups with a blank line. Use absolute imports relative to the `src` directory where possible.
* **Naming Conventions:**
    * `snake_case` for variables, functions, methods, modules.
    * `PascalCase` for classes.
    * `UPPER_SNAKE_CASE` for constants.
* **Error Handling:** Use `try...except` blocks for operations that can fail (API calls, file I/O, data parsing, calculations). Catch specific exceptions (e.g., `requests.exceptions.RequestException`, `KeyError`, `ValueError`, `ZeroDivisionError`). Log errors clearly. Implement retry logic for transient API errors if appropriate.
* **Modularity:** Structure code into logical modules (e.g., `api_clients.py`, `calculations.py`, `config.py`, `main.py`, `storage.py`, `caching.py`). Functions and classes should have single responsibilities.
* **Comments:**
    * Use docstrings (`"""..."""`) for modules, classes, functions, and methods, explaining purpose, arguments, and return values (e.g., Google or NumPy style).
    * Use inline comments (`#`) sparingly only for explaining complex or non-obvious logic.
* **Folder Structure:**
    * `src/real_estate_deal_finder/`: Main application code.
    * `tests/`: Unit and integration tests.
    * `scripts/`: Utility scripts (if any).
    * `docs/`: Documentation.

## 5. Architecture & Key Decisions

* **Configuration:** All configurable parameters (API keys, financial assumptions like default down payment %, rate, term, expenses, filter thresholds, cache duration) must be loaded from environment variables (`.env` file via `config.py`) or a dedicated config file.
* **API Interaction:** Create dedicated functions or classes (e.g., `ZillowApiClient`, `RentCastApiClient`) to handle interactions with external APIs, including request building, response parsing, and error handling.
* **Caching:** Implement 30-day caching specifically for RentCast API calls (based on ZIP code/bedroom count) to minimize API usage. Store cache data persistently (e.g., simple JSON file, SQLite).
* **Calculations:** Centralize financial calculations (mortgage, cash flow, CoC return) in a dedicated module (`calculations.py`) with clear, testable functions.
* **Output:** Generate output as a CSV file with the specified columns.

## 6. Constraints & "Do Nots"

* **Dependencies:** Do not add new third-party dependencies to `requirements.txt` without explicit discussion or approval.
* **Core Logic:** Avoid making significant changes to the core calculation logic or API interaction methods without discussion.
* **Testing:** All new functions/classes or bug fixes must include corresponding unit tests in the `tests/` directory. Aim for high test coverage (>80%).
* **Secrets:** Never hardcode API keys or other sensitive credentials. Use environment variables accessed via `config.py` only. Reference `.env.example`.
* **Blocking Operations:** Be mindful of long-running operations (especially sequential API calls for many ZIP codes). Consider asynchronous operations (`asyncio`, `aiohttp`) or concurrent execution (`concurrent.futures`) if performance becomes an issue for large batches, but start with simpler sequential logic for the MVP.

## 7. AI Assistant Persona

* Please act as a **Senior Python Developer** experienced in building data processing applications, interacting with external APIs, adhering to clean code principles (PEP 8, SOLID where applicable), and writing robust, testable code. Ask clarifying questions if requirements are ambiguous.

## 8. Providing Context with Requests

* When asking for code generation or modification, please provide:
    * Clear requirements for the specific task or function.
    * Relevant existing code snippets, function signatures, or file paths (`src/real_estate_deal_finder/...`).
    * Any specific constraints, inputs, or expected outputs for the task.