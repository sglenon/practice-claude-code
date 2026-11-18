// Build coffee.html from coffee.csv.
//
// Node.js built-in modules only. Run with:
//
//     node build.js
//
// It writes coffee.html next to this script and prints the totals.

const fs = require("fs");
const path = require("path");

const HERE = __dirname;
const COFFEE_CSV = path.join(HERE, "coffee.csv");
const COFFEE_HTML = path.join(HERE, "coffee.html");

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function loadRows(file = COFFEE_CSV) {
  const text = fs.readFileSync(file, "utf8").trim();
  const [header, ...lines] = text.split(/\r?\n/).filter((line) => line.length > 0);
  const columns = header.split(",");
  return lines.map((line) => {
    const values = line.split(",");
    const row = {};
    columns.forEach((col, i) => {
      row[col] = values[i];
    });
    return row;
  });
}

function totalsPerTeam(rows) {
  const teams = [];
  const totals = {};
  for (const row of rows) {
    const team = row.team;
    if (!teams.includes(team)) {
      teams.push(team);
      totals[team] = 0;
    }
    totals[team] += Number(row.cups);
  }
  return { teams, totals };
}

function busiestDay(rows) {
  const perDay = {};
  for (const row of rows) {
    perDay[row.day] = (perDay[row.day] || 0) + Number(row.cups);
  }
  let bestDay = null;
  let bestTotal = -1;
  for (const [day, total] of Object.entries(perDay)) {
    if (total > bestTotal) {
      bestDay = day;
      bestTotal = total;
    }
  }
  return { day: bestDay, total: bestTotal };
}

function renderHtml(rows) {
  const { teams, totals } = totalsPerTeam(rows);
  const { day, total: dayTotal } = busiestDay(rows);
  const maxTotal = Math.max(0, ...Object.values(totals));

  const bars = teams
    .map((team) => {
      const count = totals[team];
      const width = maxTotal ? Math.round((count / maxTotal) * 100) : 0;
      return (
        `<div class="bar-row"><span class="bar-label">${escapeHtml(team)}</span>` +
        `<div class="bar-track"><div class="bar-fill" style="width:${width}%;">` +
        `</div></div><span class="bar-value">${count}</span></div>`
      );
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Coffee board</title>
<style>
body { font-family: -apple-system, Helvetica, Arial, sans-serif;
  background: #f4f6f8; color: #1f2933; margin: 0; padding: 2rem; }
section { background: #fff; border-radius: 10px; max-width: 520px;
  box-shadow: 0 1px 3px rgba(0,0,0,.1); padding: 1.5rem; margin-bottom: 1.5rem; }
.bar-row { display: flex; align-items: center; margin-bottom: .6rem; }
.bar-label { width: 80px; font-weight: 600; }
.bar-track { flex: 1; background: #e4e9ef; border-radius: 6px; height: 18px;
  margin: 0 .75rem; overflow: hidden; }
.bar-fill { background: #d97706; height: 100%; border-radius: 6px; }
.bar-value { width: 28px; text-align: right; }
</style>
</head>
<body>
  <h1>Coffee board</h1>
  <section>
    <h2>Total cups per team</h2>
    ${bars}
  </section>
  <section>
    <h2>Busiest day</h2>
    <p>${escapeHtml(day)} with ${dayTotal} cups.</p>
  </section>
</body>
</html>
`;
}

function main() {
  const rows = loadRows();
  const { teams, totals } = totalsPerTeam(rows);
  const { day, total: dayTotal } = busiestDay(rows);

  fs.writeFileSync(COFFEE_HTML, renderHtml(rows), "utf8");

  console.log(`Wrote ${COFFEE_HTML}`);
  for (const team of teams) {
    console.log(`${team}: ${totals[team]} cups`);
  }
  console.log(`Busiest day: ${day} (${dayTotal} cups)`);
}

main();
