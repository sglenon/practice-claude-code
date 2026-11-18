"""Tests for board/make_board.py.

Run with:

    python3 -m unittest discover -s board -v
"""

import unittest

import make_board


class TestMakeBoard(unittest.TestCase):
    def test_load_tickets_has_fourteen_rows(self):
        tickets = make_board.load_tickets()
        self.assertEqual(len(tickets), 14)

    def test_open_per_team_counts(self):
        tickets = make_board.load_tickets()
        counts = make_board.open_per_team(tickets)
        self.assertEqual(
            counts,
            {"Web": 1, "Data": 1, "Ops": 2, "Sec": 1},
        )

    def test_render_html_has_every_team_name(self):
        tickets = make_board.load_tickets()
        page = make_board.render_html(tickets)
        for team in ("Web", "Data", "Ops", "Sec"):
            self.assertIn(team, page)


if __name__ == "__main__":
    unittest.main()
