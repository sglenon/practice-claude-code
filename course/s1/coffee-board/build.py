"""Build coffee.html from coffee.csv.

Standard library only. Run with:

    python3 build.py

It writes coffee.html next to this script and prints the totals.
"""

import csv
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
COFFEE_CSV = os.path.join(HERE, "coffee.csv")
COFFEE_HTML = os.path.join(HERE, "coffee.html")


def load_rows(path=COFFEE_CSV):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def totals_per_team(rows):
    teams = []
    totals = {}
    for row in rows:
        team = row["team"]
        if team not in teams:
            teams.append(team)
            totals[team] = 0
        totals[team] += int(row["cups"])
    return teams, totals


def busiest_day(rows):
    per_day = {}
    for row in rows:
        per_day[row["day"]] = per_day.get(row["day"], 0) + int(row["cups"])
    return max(per_day.items(), key=lambda item: item[1])


def render_html(rows):
    teams, totals = totals_per_team(rows)
    day, day_total = busiest_day(rows)
    max_total = max(totals.values(), default=0)

    bars = []
    for team in teams:
        count = totals[team]
        width = round((count / max_total) * 100) if max_total else 0
        bars.append(
            f'<div class="bar-row"><span class="bar-label">{html.escape(team)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%;">'
            f'</div></div><span class="bar-value">{count}</span></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Coffee board</title>
<style>
body {{ font-family: -apple-system, Helvetica, Arial, sans-serif;
  background: #f4f6f8; color: #1f2933; margin: 0; padding: 2rem; }}
section {{ background: #fff; border-radius: 10px; max-width: 520px;
  box-shadow: 0 1px 3px rgba(0,0,0,.1); padding: 1.5rem; margin-bottom: 1.5rem; }}
.bar-row {{ display: flex; align-items: center; margin-bottom: .6rem; }}
.bar-label {{ width: 80px; font-weight: 600; }}
.bar-track {{ flex: 1; background: #e4e9ef; border-radius: 6px; height: 18px;
  margin: 0 .75rem; overflow: hidden; }}
.bar-fill {{ background: #d97706; height: 100%; border-radius: 6px; }}
.bar-value {{ width: 28px; text-align: right; }}
</style>
</head>
<body>
  <h1>Coffee board</h1>
  <section>
    <h2>Total cups per team</h2>
    {''.join(bars)}
  </section>
  <section>
    <h2>Busiest day</h2>
    <p>{html.escape(day)} with {day_total} cups.</p>
  </section>
</body>
</html>
"""


def main():
    rows = load_rows()
    teams, totals = totals_per_team(rows)
    day, day_total = busiest_day(rows)

    with open(COFFEE_HTML, "w", encoding="utf-8") as fh:
        fh.write(render_html(rows))

    print(f"Wrote {COFFEE_HTML}")
    for team in teams:
        print(f"{team}: {totals[team]} cups")
    print(f"Busiest day: {day} ({day_total} cups)")


if __name__ == "__main__":
    main()
