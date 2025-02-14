from include.utils import get_raw_audio_bq_schema


def test_get_raw_audio_bq_schema():
    """Test the schema for the raw_audio table"""
    schema = get_raw_audio_bq_schema()

    assert isinstance(schema, list), "Schema should be a list"
    assert len(schema) == 19, "Schema should contain 19 fields"

    expected_fields = {
        "ingestion_timestamp": "TIMESTAMP",
        "yt_video_title": "STRING",
        "title": "STRING",
        "filename": "STRING",
        "format_name": "STRING",
        "sample_rate": "INTEGER",
        "channels": "INTEGER",
        "bits_per_sample": "INTEGER",
        "duration": "FLOAT",
        "bit_rate": "INTEGER",
        "size": "INTEGER",
        "codec_name": "STRING",
        "min_speakers": "INTEGER",
        "max_speakers": "INTEGER",
        "team": "STRING",
        "text": "STRING",
        "gpt_clarity": "INTEGER",
        "gpt_intensity": "INTEGER",
        "gpt_summary": "STRING",
    }

    for field in schema:
        assert "name" in field, "Each schema entry must have a 'name'"
        assert "type" in field, "Each schema entry must have a 'type'"
        assert "mode" in field, "Each schema entry must have a 'mode'"
        assert "description" in field, "Each schema entry must have a 'description'"

        field_name = field["name"]
        assert field_name in expected_fields, f"Unexpected field: {field_name}"
        assert (
            field["type"] == expected_fields[field_name]
        ), f"Type mismatch for field {field_name}"
