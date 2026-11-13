"""Sensor report for the Session 1 data option. Python 3 standard library only."""
import csv
from pathlib import Path

DATA = Path(__file__).with_name("readings.csv")


def load_values(path, column):
    with open(path, newline="") as f:
        return [float(row[column]) for row in csv.DictReader(f)]


def mean(values):
    return sum(values) / len(values)


if __name__ == "__main__":
    values = load_values(DATA, "reading")
    print(f"count\t{len(values)}")
    print(f"mean\t{mean(values):.2f}")
