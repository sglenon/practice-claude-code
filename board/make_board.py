"""Build a ticket board page from board/tickets.csv.

Standard library only. Run with:

    python3 board/make_board.py

It writes board/out/board.html and prints the open/closed totals
per team.
"""

from __future__ import annotations

import csv
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TICKETS_CSV = os.path.join(HERE, "tickets.csv")
OUT_DIR = os.path.join(HERE, "out")
OUT_HTML = os.path.join(OUT_DIR, "board.html")

STYLE = """
body { font-family: -apple-system, Helvetica, Arial, sans-serif;
  background: #f4f6f8; color: #1f2933; margin: 0; padding: 2rem; }
section { background: #fff; border-radius: 10px; max-width: 640px;
  box-shadow: 0 1px 3px rgba(0,0,0,.1); padding: 1.5rem; margin-bottom: 1.5rem; }
.bar-row { display: flex; align-items: center; margin-bottom: .6rem; }
.bar-label { width: 70px; font-weight: 600; }
.bar-track { flex: 1; background: #e4e9ef; border-radius: 6px; height: 18px;
  margin: 0 .75rem; overflow: hidden; }
.bar-fill { background: #3b82f6; height: 100%; border-radius: 6px; }
.bar-value { width: 24px; text-align: right; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: .5rem .75rem; border-bottom: 1px solid #e4e9ef; }
th { color: #52606d; font-size: .85rem; text-transform: uppercase; }
ul { list-style: none; margin: 0; padding: 0; }
li { display: flex; gap: .75rem; align-items: center; padding: .5rem 0;
  border-bottom: 1px solid #e4e9ef; }
.ticket-id { font-weight: 600; width: 48px; }
.ticket-team { width: 60px; color: #52606d; }
.ticket-priority { border-radius: 4px; padding: .1rem .5rem; font-size: .8rem;
  text-transform: capitalize; }
.priority-high { background: #fde2e1; color: #b42318; }
.priority-medium { background: #fef0c7; color: #93590b; }
.priority-low { background: #e3f5e8; color: #1b7a3d; }
.ticket-opened { margin-left: auto; color: #7b8794; font-size: .85rem; }
"""


def load_tickets(path: str = TICKETS_CSV) -> list[dict]:
    """Read tickets.csv and return a list of ticket dicts.

    Each dict has keys: id, team, priority, opened, closed. The
    "closed" value is an empty string for tickets that are still open.
    """
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def team_order(tickets: list[dict]) -> list[str]:
    """Return team names in order of first appearance."""
    order = []
    for ticket in tickets:
        if ticket["team"] not in order:
            order.append(ticket["team"])
    return order


def open_per_team(tickets: list[dict]) -> dict[str, int]:
    """Count open (not yet closed) tickets per team."""
    counts: dict[str, int] = {}
    for ticket in tickets:
        if not ticket["closed"]:
            counts[ticket["team"]] = counts.get(ticket["team"], 0) + 1
    return counts


def closed_per_team(tickets: list[dict]) -> dict[str, int]:
    """Count closed tickets per team."""
    counts: dict[str, int] = {}
    for ticket in tickets:
        if ticket["closed"]:
            counts[ticket["team"]] = counts.get(ticket["team"], 0) + 1
    return counts


def render_html(tickets: list[dict]) -> str:
    """Render the full board page as an HTML string."""
    teams = team_order(tickets)
    open_counts = open_per_team(tickets)
    closed_counts = closed_per_team(tickets)
    max_open = max(open_counts.values(), default=0)

    bars = []
    for team in teams:
        count = open_counts.get(team, 0)
        width = int((count / max_open) * 100) if max_open else 0
        bars.append(
            f'<div class="bar-row"><span class="bar-label">{html.escape(team)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%;">'
            f'</div></div><span class="bar-value">{count}</span></div>'
        )

    rows = []
    for team in teams:
        rows.append(
            f"<tr><td>{html.escape(team)}</td><td>{open_counts.get(team, 0)}</td>"
            f"<td>{closed_counts.get(team, 0)}</td></tr>"
        )

    items = []
    for ticket in tickets:
        if ticket["closed"]:
            continue
        items.append(
            f'<li><span class="ticket-id">{html.escape(ticket["id"])}</span>'
            f'<span class="ticket-team">{html.escape(ticket["team"])}</span>'
            f'<span class="ticket-priority priority-{html.escape(ticket["priority"])}">'
            f'{html.escape(ticket["priority"])}</span>'
            f'<span class="ticket-opened">opened {html.escape(ticket["opened"])}</span></li>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ticket board</title>
<style>{STYLE}</style>
</head>
<body>
  <h1>Ticket board</h1>
  <section>
    <h2>Open tickets per team</h2>
    {''.join(bars)}
  </section>
  <section>
    <h2>Team summary</h2>
    <table>
      <thead><tr><th>Team</th><th>Open</th><th>Closed</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
  </section>
  <section>
    <h2>Open tickets</h2>
    <ul>{''.join(items)}</ul>
  </section>
</body>
</html>
"""


def main() -> None:
    tickets = load_tickets()
    teams = team_order(tickets)
    open_counts = open_per_team(tickets)
    closed_counts = closed_per_team(tickets)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(render_html(tickets))

    print(f"Wrote {OUT_HTML}")
    for team in teams:
        print(f"{team}: open={open_counts.get(team, 0)} closed={closed_counts.get(team, 0)}")


if __name__ == "__main__":
    main()
