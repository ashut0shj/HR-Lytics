# Version Control & Deployment

## 1. Branching Model

```
main                              -- always deployable
 ├── feature/database-design       -- OLTP + OLAP DDL, diagrams
 ├── feature/data-synthesizer      -- pandas/Faker scaling + SCD2 seeding
 ├── feature/etl-pipeline          -- stored procedures, CTEs, window fns
 ├── feature/python-oop-backend    -- db_manager, models, managers
 ├── feature/streamlit-dashboard   -- app/ pages
 └── feature/deployment            -- Streamlit Cloud config, secrets setup
 ├── F-01-repo-scaffold            -- README, CONTRIBUTING, CODE_OF_CONDUCT, folder layout
 ├── F-02-oltp-database-design    -- OLTP + OLAP DDL, diagrams
 ├── F-03-data-synthesizer        -- pandas/Faker scaling + SCD2 seeding
 ├── F-04-olap-star-schema        -- Dimensional warehouse tables
 ├── F-05-etl-pipeline            -- stored procedures, CTEs, window fns
 ├── F-06-python-backend          -- db_manager, models, managers
 ├── F-07-streamlit-dashboard     -- app/ pages
 └── F-08-deployment              -- Streamlit Cloud config, secrets setup
```

- Never commit directly to `main`.
- Each feature branch → Pull Request → review (self-review is fine for
  solo work, but write a real PR description) → merge.
- Keep PRs scoped to one phase/subsystem so history stays readable — this
  matters for the "strict version control" evaluation point.
- Feature branches are named `F-xx-<name>`.
- Each feature branch → Pull Request → review → merge.
- Keep PRs scoped to one phase/subsystem so history stays readable.

## 2. Commit Hygiene

- Small, descriptive commits over one giant commit per branch:
  `feat: add Dim_Employee DDL with SCD2 columns`,
  `fix: correct FK direction in Assignment table`.
- Don't commit generated artifacts that can be regenerated
  (`data/synthesized/*.csv` if large — see `.gitignore` in
  `01_FOLDER_STRUCTURE.md`), don't commit `.env`/`secrets.toml`.
- Commits follow `vY.XX.ZZ-message` format (e.g., `v0.01.01-docs: create README and guidelines`, `v0.02.01-feat: add Dim_Employee DDL`).
- Small, descriptive commits over one giant commit per branch.
- Don't commit generated artifacts that can be regenerated (`data/synthesized/*.csv`), don't commit `.env`/`secrets.toml`.

## 3. PR Checklist (use as a PR template)

- [ ] Code runs locally without errors
- [ ] SQL scripts tested against a local MySQL instance
- [ ] README/docs updated if this PR changes setup steps or architecture
- [ ] No secrets/credentials committed
- [ ] Linked to relevant phase in `00_MASTER_PLAN.md`

## 4. Streamlit Community Cloud Deployment

1. Push final `main` branch to GitHub (public or accessible repo).
2. On share.streamlit.io: "New app" → select repo, branch (`main`), and
   entry point (`app/Home.py`).
3. In the app's **Secrets** panel, add MySQL connection details matching
   what `db_manager.py` expects (host, user, password, database, port).
   Note: this means your MySQL instance must be reachable from the
   public internet (cloud-hosted MySQL — e.g. a free-tier RDS,
   PlanetScale, or similar — not `localhost`).
4. Confirm `requirements.txt` is complete and pinned (Streamlit Cloud
   builds from it fresh — a missing dependency here is the most common
   deploy failure).
5. After deploy, smoke-test both a write flow (onboard an employee) and
   a read flow (load a dashboard) against the live public URL.

## 5. Local vs. Cloud Config Split

Keep `db_manager.py` environment-agnostic by checking for `st.secrets`
first and falling back to `.env`/`os.environ`, so the same codebase runs
unmodified locally and on Streamlit Cloud. Document both setups in
`docs/SETUP.md`.
