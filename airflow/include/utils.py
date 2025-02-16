import json
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
from airflow.exceptions import AirflowSkipException
import logging

logger = logging.getLogger(__name__)


def get_raw_audio_bq_schema() -> list[dict]:
    """Get the BigQuery schema for the raw audio table"""

    return [
        {
            "name": "ingestion_timestamp",
            "type": "TIMESTAMP",
            "mode": "REQUIRED",
            "description": "Timestamp of when the data was ingested",
        },
        {
            "name": "yt_video_title",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "Title of the YouTube video",
        },
        {
            "name": "title",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "Title of the segment",
        },
        {
            "name": "filename",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "Filename of the audio segment",
        },
        {
            "name": "format_name",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "Format of the audio segment",
        },
        {
            "name": "sample_rate",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Sample rate of the audio segment",
        },
        {
            "name": "channels",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Number of channels in the audio segment",
        },
        {
            "name": "bits_per_sample",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Bits per sample in the audio segment",
        },
        {
            "name": "duration",
            "type": "FLOAT",
            "mode": "REQUIRED",
            "description": "Duration of the audio segment",
        },
        {
            "name": "bit_rate",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Bit rate of the audio segment",
        },
        {
            "name": "size",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Size of the audio segment",
        },
        {
            "name": "codec_name",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "Codec name of the audio segment",
        },
        {
            "name": "min_speakers",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Minimum number of speakers in the audio segment",
        },
        {
            "name": "max_speakers",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Maximum number of speakers in the audio segment",
        },
        {
            "name": "team",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "Team name",
        },
        {
            "name": "text",
            "type": "STRING",
            "mode": "NULLABLE",
            "description": "Transcription of the audio segment",
        },
        {
            "name": "gpt_clarity",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Clarity rating of the audio segment",
        },
        {
            "name": "gpt_intensity",
            "type": "INTEGER",
            "mode": "REQUIRED",
            "description": "Intensity rating of the audio segment",
        },
        {
            "name": "gpt_summary",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "Summary of the audio segment",
        },
    ]


def get_gpt_summary(text: str) -> dict:
    """
    Get a summary of the input text using the GPT-4o-mini model.

    Args:
        text (str): The input text to summarize.

    Returns:
        dict: A dictionary containing the clarity and intensity ratings, and a summary of the input text.
    """

    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You analyze transcribed text from a LoL Esports game and extract emotional states "
                    "expressed by players or casters. Identify emotions such as confusion and "
                    "intensity, and associate them with a rating from 1 (low) to 5 (high). If the text "
                    "is empty or the text is less than 50 characters, please provide a -1 rating "
                    "for both clarity and intensity. "
                ),
            },
            {"role": "user", "content": text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "lol_emotion_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "clarity": {
                            "description": "How clear was the communication on a scale of 1 (low) to 5 (high). -1 if input text is empty.",
                            "type": "integer",
                            "enum": [-1, 1, 2, 3, 4, 5],
                        },
                        "intensity": {
                            "description": "Intensity of the emotion on a scale of 1 (low) to 5 (high). -1 if input text is empty.",
                            "type": "integer",
                            "enum": [-1, 1, 2, 3, 4, 5],
                        },
                        "summary": {
                            "description": "Summary of the input text.",
                            "type": "string",
                        },
                    },
                    "required": ["clarity", "intensity", "summary"],
                    "additionalProperties": False,
                },
            },
        },
    )
    response = json.loads(response.choices[0].message.content)

    if (
        response["clarity"] is None
        or response["intensity"] is None
        or response["summary"] is None
        or len(response) != 3
    ):
        logger.error(
            "Response should contain clarity, intensity, and summary. Response: {response}"
        )
        raise ValueError(
            "Response should contain clarity, intensity, and summary. Response: {response}"
        )

    return response


def clean_yt_title(title: str) -> str:
    """
    Cleans a YouTube video title by removing special characters and limiting the length to 15 characters.

    Args:
        title (str): The YouTube video title to clean.

    Returns:
        str: The cleaned YouTube video title.
    """

    if not title:
        logger.error("Title cannot be empty")
        raise ValueError("Title cannot be empty")

    title = title.strip()
    title = "".join(e for e in title if e.isalnum())
    logger.debug(f"Cleaned YouTube video title: {title}")
    return title


def get_segment_metadata(
    audio_info: dict,
    title: str,
    filename: str,
    audio_metadata: dict,
    team: str = "Los Ratones",
) -> dict:
    """
    Get metadata for an audio segment

    Args:
        audio_info (dict): The output of the download_audio task.
        title (str): Title of the segment.
        filename (str): Filename of the audio segment.
        audio_metadata (dict): Audio metadata from pydub.
        team (str, optional): Defaults to 'Los Ratones'.

    Returns:
        dict: A dictionary containing metadata for the audio segment.
    """
    return {
        "yt_video_title": audio_info["yt_video_title"],
        "title": title,
        "filename": filename,
        "format_name": audio_metadata["format_name"],
        "sample_rate": audio_metadata["sample_rate"],
        "channels": audio_metadata["channels"],
        "bits_per_sample": audio_metadata["bits_per_sample"],
        "duration": audio_metadata["duration"],
        "bit_rate": audio_metadata["bit_rate"],
        "size": audio_metadata["size"],
        "codec_name": audio_metadata["codec_name"],
        "min_speakers": 5,
        "max_speakers": -1,
        "team": team,  # TODO: need to make dynamic to scale. Good for now
    }


def scrape_team_data(team_name: str) -> str:
    """
    Scrapes the team members from the Fandom wiki page for the given team name.

    Args:
        team_name (str): The name of the team to scrape.

    Returns:
        str: The SQL query to insert the scraped data into BigQuery.
    """
    url = f"https://lol.fandom.com/wiki/{team_name}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find("table", {"class": "wikitable"})

    if table is None:
        raise AirflowSkipException(f"Could not find team members table for {team_name}")

    rows = []
    for tr in table.find_all("tr")[1:]:
        cols = tr.find_all(["td", "th"])
        if len(cols) >= 4:
            name_cell = cols[2].text.strip().replace("'", "\\'")
            team_cell = team_name.replace("'", "\\'")
            rows.append(
                f"STRUCT('{name_cell}' as player_name, '{team_cell}' as team, "
                f"CURRENT_DATE() as effective_start_date, CAST(NULL AS DATE) as effective_end_date, "
                f"TRUE as is_current, CURRENT_TIMESTAMP() as created_at, "
                f"CURRENT_TIMESTAMP() as updated_at)"
            )

    if len(rows) < 5:
        raise AirflowSkipException(
            f"Could not find enough team members for {team_name}"
        )

    values = ",\n                ".join(rows)

    sql_query = f"""
        MERGE `lolesports_voice_analytics.team_members` AS target
        USING (
            SELECT
                source.player_name,
                source.team,
                source.effective_start_date,
                source.effective_end_date,
                source.is_current,
                source.created_at,
                source.updated_at
            FROM UNNEST([
                {values}
            ]) AS source
        ) AS source
        ON target.player_name = source.player_name AND target.is_current
        WHEN MATCHED AND target.team != source.team THEN
            UPDATE SET
                effective_end_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY),
                is_current = FALSE,
                updated_at = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN
            INSERT (
                player_name,
                team,
                effective_start_date,
                effective_end_date,
                is_current,
                created_at,
                updated_at
            )
            VALUES (
                source.player_name,
                source.team,
                source.effective_start_date,
                CAST(NULL AS DATE),
                source.is_current,
                CURRENT_TIMESTAMP(),
                CURRENT_TIMESTAMP()
            )
    """

    logger.debug(sql_query)

    return sql_query
