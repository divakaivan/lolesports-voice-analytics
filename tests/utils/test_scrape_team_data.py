import unittest
from unittest.mock import patch, MagicMock
import requests
from include.utils import scrape_team_data


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
        with self.assertRaises(ValueError) as context:
            scrape_team_data(team_name)

        self.assertEqual(
            str(context.exception), "Could not find team members table for T1"
        )

    @patch("requests.get")
    def test_scrape_team_data_invalid_response(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")
        team_name = "T1"

        with self.assertRaises(requests.RequestException):
            scrape_team_data(team_name)


if __name__ == "__main__":
    unittest.main()
