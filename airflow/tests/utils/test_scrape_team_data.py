import unittest
from unittest.mock import patch, MagicMock
from include.utils import scrape_team_data
from airflow.exceptions import AirflowSkipException  # noqa: F401


def mock_fandom_response(html_content):
    mock_response = MagicMock()
    mock_response.content = html_content.encode("utf-8")
    return mock_response


class TestScrapeTeamData(unittest.TestCase):
    @patch("requests.get")
    def test_scrape_team_data_success(self, mock_get):
        html_content = """
        <table class="wikitable">
            <tr>
                <th>Column1</th><th>Column2</th><th>Player Name</th><th>Column4</th>
            </tr>
            <tr>
                <td>Data1</td><td>Data2</td><td>Faker</td><td>Data4</td>
            </tr>
            <tr>
                <td>Data1</td><td>Data2</td><td>Caps</td><td>Data4</td>
            </tr>
            <tr>
                <td>Data1</td><td>Data2</td><td>Nemesis</td><td>Data4</td>
            </tr>
            <tr>
                <td>Data1</td><td>Data2</td><td>Rekkles</td><td>Data4</td>
            </tr>
            <tr>
                <td>Data1</td><td>Data2</td><td>Caedrel</td><td>Data4</td>
            </tr>
        </table>
        """
        mock_get.return_value = mock_fandom_response(html_content)

        team_name = "T1"
        sql_query = scrape_team_data(team_name)

        self.assertIn("Faker", sql_query)
        self.assertIn("Caps", sql_query)
        self.assertIn("T1", sql_query)
        self.assertIn("MERGE", sql_query)

    @patch("requests.get")
    def test_scrape_team_data_no_table(self, mock_get):
        html_content = "<html><body><p>No team table here</p></body></html>"
        mock_get.return_value = mock_fandom_response(html_content)

        team_name = "T1"

        with self.assertRaises(AirflowSkipException) as context:
            scrape_team_data(team_name)

        self.assertEqual(
            str(context.exception), "Could not find team members table for T1"
        )


if __name__ == "__main__":
    unittest.main()
