import os
from pathlib import Path

import logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s]:%(message)s:")

list_of_files = [
    ".github/workflows/.gitkeep",
    "backend/src/__init__.py",
    "backend/src/graph/__init__.py",
    "backend/src/tools/__init__.py",
    "backend/src/state/__init__.py",
    "backend/data/",
    "backend/api/",
    "backend/tests/",
    "backend/Dockerfile",
    "backend/.env",
    ".github/workflows/ci.yaml"]


for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
        logging.info(f"Creating directory: {filedir} for the file: {filename}")

    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, "w") as f:
            pass  # Create an empty file
            logging.info(f"Creating empty file: {filename}")
    else:
        logging.info(f"{filename} already exists and is not empty. Skipping file creation.")
