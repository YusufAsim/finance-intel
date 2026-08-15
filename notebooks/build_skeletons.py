"""Write the four notebook skeletons.

Kept in the repository so the skeletons can be regenerated without hand
editing json.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent

NOTEBOOKS = {
    "01_categorization": {
        "title": "Categorization",
        "goal": "Predict the spending category of a transaction from its raw"
        " description.",
        "metrics": "accuracy, macro f1, per category precision and recall,"
        " confusion matrix",
        "artifact": "category_model_v1.joblib",
    },
    "02_recurring": {
        "title": "Recurring payments",
        "goal": "Group transactions into recurring series and describe their"
        " cadence.",
        "metrics": "series level precision and recall against series_id,"
        " cadence accuracy",
        "artifact": "recurring_model_v1.joblib",
    },
    "03_anomaly": {
        "title": "Anomaly detection",
        "goal": "Score how far a transaction sits from the usual pattern.",
        "metrics": "precision at k, recall on planted anomalies, roc auc",
        "artifact": "anomaly_model_v1.joblib",
    },
    "04_forecast": {
        "title": "Cash flow forecast",
        "goal": "Project the account balance over the coming days.",
        "metrics": "mae and mape per horizon, coverage of the interval",
        "artifact": "forecast_model_v1.joblib",
    },
}

LOAD_DATA = """\
# Load a generated statement. Run the generator first:
#   uv run --directory ../data python -m generator --seed 42 --profile all \\
#       --months 24 --out out
import json
from pathlib import Path

DATA_DIR = Path("../data/out")
PROFILE = "employee"
SEED = 42

transactions = json.loads(
    (DATA_DIR / f"transactions_{PROFILE}_{SEED}.json").read_text(encoding="utf-8")
)
print(f"{len(transactions)} transactions loaded")
transactions[:2]
"""

LOAD_LABELS = """\
# Ground truth produced in the same run as the statement above.
labels = json.loads(
    (DATA_DIR / f"labels_{PROFILE}_{SEED}.json").read_text(encoding="utf-8")
)
by_id = {row["transaction_id"]: row for row in labels}
assert len(by_id) == len(transactions), "labels and transactions must line up"
print(f"{len(labels)} labels loaded")
labels[:2]
"""

SAVE_ARTIFACT = """\
# Save the trained model where the ml service looks for it.
ARTIFACTS_DIR = Path("../ml/artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_PATH = ARTIFACTS_DIR / ARTIFACT_NAME

# import joblib
# joblib.dump(model, ARTIFACT_PATH)
print(f"artifact target: {ARTIFACT_PATH}")
"""


def markdown(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(True),
    }


def with_ids(cells: list[dict]) -> list[dict]:
    """Stamp every cell with the id recent nbformat versions expect."""
    for position, cell in enumerate(cells, start=1):
        cell["id"] = f"cell-{position:02d}"
    return cells


def build(name: str, spec: dict) -> dict:
    return {
        "cells": with_ids([
            markdown(
                f"# {spec['title']}\n"
                "\n"
                f"**Goal.** {spec['goal']}\n"
                "\n"
                "This notebook is a skeleton. Model code goes into the sections\n"
                "marked below.\n"
            ),
            markdown("## Load the statement\n"),
            code(LOAD_DATA),
            markdown("## Load the ground truth\n"),
            code(LOAD_LABELS),
            markdown(
                "## Features and model\n"
                "\n"
                "Model code goes here. Nothing is implemented yet.\n"
            ),
            code("# feature engineering and training go here\n"),
            markdown(
                "## Evaluation\n"
                "\n"
                f"Metrics to report: {spec['metrics']}.\n"
                "\n"
                "Evaluation code goes here. Nothing is implemented yet.\n"
            ),
            code("# evaluation against the ground truth goes here\n"),
            markdown("## Save the artifact\n"),
            code(f'ARTIFACT_NAME = "{spec["artifact"]}"\n'),
            code(SAVE_ARTIFACT),
        ]),
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    for name, spec in NOTEBOOKS.items():
        path = HERE / f"{name}.ipynb"
        payload = json.dumps(build(name, spec), indent=1, ensure_ascii=False) + "\n"
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
        print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
