# Makefile for GitGuard


# === Variables ===
VENV_NAME=venv


# === Phony Targets ===
.PHONY: venv install freeze clean cleanup


# === Targets ===

# venv commands
venv:
	python3 -m venv $(VENV_NAME)

install:
	source $(VENV_NAME)/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

freeze:
	source $(VENV_NAME)/bin/activate && pip freeze > requirements.txt

clean:
	rm -rf $(VENV_NAME)

# Cleanup __pycache__ directories
cleanup:
	find . -type d -name "__pycache__" -exec rm -r {} +
