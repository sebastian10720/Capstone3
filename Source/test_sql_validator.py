import unittest

from agents.sql_agent import validate_sql


class TestSQLValidator(unittest.TestCase):
    def test_allows_select(self):
        self.assertTrue(validate_sql("SELECT id FROM projects")["valid"])

    def test_blocks_destructive_statement(self):
        self.assertFalse(validate_sql("DELETE FROM projects")["valid"])

    def test_allows_column_containing_blocked_word(self):
        self.assertTrue(validate_sql("SELECT deleted_at FROM projects")["valid"])

    def test_blocks_stacked_query_with_blocked_keyword(self):
        self.assertFalse(
            validate_sql("SELECT id FROM projects; DROP TABLE clients")["valid"]
        )

    def test_blocks_stacked_selects(self):
        self.assertFalse(
            validate_sql("SELECT id FROM projects; SELECT id FROM clients")["valid"]
        )


if __name__ == "__main__":
    unittest.main()