import os

SQL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql")

def load(relative_path):
    full_path = os.path.join(SQL_DIR, relative_path)
    with open(full_path, "r") as f:
        return f.read()

def load_named(relative_path, name):
    content = load(relative_path)
    queries = {}
    current_name = None
    current_lines = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            if current_name and current_lines:
                queries[current_name] = "\n".join(current_lines).strip()
            current_name = stripped[2:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_name and current_lines:
        queries[current_name] = "\n".join(current_lines).strip()

    if name not in queries:
        raise KeyError(f"Query '{name}' not found in {relative_path}")

    return queries[name]

