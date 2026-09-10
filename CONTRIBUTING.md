# HR-Lytics — Contributing Guidelines

Thank you for contributing to **HR-Lytics**! This guide outlines the workflow, version control practices, branch naming rules, and code standards for the V4C Data Engineering training exercise.

---

## 🌿 Version Control & Branching Strategy

To maintain a clean and trackable Git history, all contributors must adhere to strict feature branching and commit message conventions.

### 1. Feature Branch Naming (`F-xx-<name>`)

Never commit directly to the `main` branch. All development work must take place on dedicated feature branches named using the format:

```text
F-xx-<name>
```

- **`F-`**: Stands for **Feature**.
- **`xx`**: Two-digit phase or feature sequence number (e.g., `01`, `02`, `03`).
- **`<name>`**: A concise, hyphen-separated description of the feature or component.

#### Examples:
- `F-01-repo-scaffold`
- `F-02-oltp-database-design`
- `F-03-data-synthesizer`
- `F-04-olap-star-schema`
- `F-05-etl-pipeline`
- `F-06-python-backend`
- `F-07-streamlit-dashboard`

---

### 2. Commit Message Convention (`vY.XX.ZZ-message`)

Commits must follow a structured versioning format to correlate individual commits with training milestones:

```text
vY.XX.ZZ-message
```

#### Version Breakdown:
- **`Y`**: Major project milestone version (e.g., `0` for development, `1` for initial release).
- **`XX`**: Feature/Phase sequence number corresponding to the feature branch.
- **`ZZ`**: Incrementing commit sequence number within that feature phase (`01`, `02`, `03`, ...).
- **`message`**: Concise description of changes.

#### Semantic Categories (Recommended prefixes in message):
- `feat`: New feature or module added.
- `fix`: Bug fix or schema correction.
- `docs`: Documentation updates (`README.md`, `Planning_docs/`, comments).
- `refactor`: Code or SQL optimization without functionality change.
- `test`: Unit tests or test scripts added/modified.

#### Commit Examples:
- `v0.01.01-docs: create README and contributing guidelines`
- `v0.02.01-feat: add OLTP DDL for employee and department tables`
- `v0.02.02-fix: resolve FK constraint in project_assignment schema`
- `v0.03.01-feat: add Faker script for 100k employee row synthesis`
- `v0.05.01-feat: implement sp_load_dim_employee_scd2 stored procedure`

---

## 🔄 Development & PR Workflow

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/<your-username>/HR-Lytics.git
   cd HR-Lytics
   ```

2. **Create a Feature Branch:**
   ```bash
   git checkout -b F-01-repo-scaffold
   ```

3. **Make Changes & Commit:**
   Ensure your code runs and tests pass locally before committing.
   ```bash
   git add .
   git commit -m "v0.01.01-docs: create initial README and guidelines"
   ```

4. **Push Branch & Open Pull Request:**
   ```bash
   git push origin F-01-repo-scaffold
   ```
   Open a Pull Request (PR) on GitHub targeting `main`.

5. **PR Checklist:**
   - [ ] Branch follows `F-xx-<name>` naming rule.
   - [ ] Commits follow `vY.XX.ZZ-message` format.
   - [ ] Code runs locally without errors.
   - [ ] SQL scripts are syntax-checked against MySQL.
   - [ ] Documentation updated if necessary.
   - [ ] No secrets or `.env` files committed.

---

## 📐 Code Style & Best Practices

- **Python:** Follow PEP 8 guidelines. Write clear docstrings for classes and methods. Use type hints where appropriate.
- **SQL:** Standardized SQL keywords in UPPERCASE (`SELECT`, `INSERT`, `CREATE TABLE`). Use prefix `sp_` for stored procedures.
- **Documentation:** Maintain markdown links and preserve references to `Planning_docs/`.

