"""
Transcribe a YouTube playlist of League of Legends.
Requies high memory and CPU to utilise mapped tasks.
"""

import os
from airflow.decorators import dag, task
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.exceptions import AirflowSkipException
from datetime import datetime, timedelta
from pytubefix import YouTube, Channel
from pydub import AudioSegment
from pydub.utils import mediainfo
from include.utils import (
    clean_yt_title,
    get_gpt_summary,
    get_segment_metadata,
    get_raw_audio_bq_schema,
)
import whisper
import json
import logging

logger = logging.getLogger(__name__)


@dag(
    dag_id="transcribe_playlist",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2024, 2, 13),
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    schedule_interval=None,
    catchup=False,
    tags=["ivan", "youtube", "transcription", "playlist"],
)
def youtube_transcription():
    @task
    def check_if_videos_already_processed() -> bool:
        """
        Check if the video has already been processed by querying BigQuery.
        Returns True if video exists, False otherwise.
        """
        ch = Channel("https://www.youtube.com/@Nemesis2_lol")
        video_urls = ch.playlists[0].video_urls
        unprocessed_videos = []
        for video_url in video_urls:
            yt = YouTube(video_url)
            video_title = clean_yt_title(yt.title)
            bq_hook = BigQueryHook()
            sql = f"""
                SELECT COUNT(*) as count
                FROM lolesports_voice_analytics.raw_data_from_video
                WHERE yt_video_title = '{video_title}'
            """
            logger.debug(f"Scheduling SQL: {sql}")
            result = bq_hook.get_first(sql)
            logger.debug(f"Result: {result}")
            count = result[0] if result else 0

            if count == 0:
                logger.debug(f"Video {video_title} has not been processed yet")
                unprocessed_videos.append(video_url)

        if not unprocessed_videos:
            raise AirflowSkipException(
                "All videos in the playlist have been processed."
            )

        return unprocessed_videos

    @task
    def data_quality_check(video_urls) -> bool:
        """
        Run a data quality check on the video details before processing
        """
        valid_videos_urls = []
        for video_url in video_urls:
            logger.info(f"Downloading audio for video: {video_url}")

            yt = YouTube(video_url)
            if yt.length < 3600 or not any(
                chapter.title.startswith("Game ") for chapter in yt.chapters
            ):
                logger.error(
                    f"Video {video_url} is less than 1 hour long or does not contain any game chapters. Skipping processing."
                )
                # raise AirflowSkipException(
                #     f"Video {video_url} does not contain any game chapters. Skipping processing."
                # )
            else:
                valid_videos_urls.append(video_url)

        return valid_videos_urls

    @task(max_active_tis_per_dag=4)
    def download_audios(video_url) -> dict:
        """
        Fetches a YouTube video from the given URL, downloads its audio as an MP4 file,
        and extracts chapter details including title, start time, and end time.

        Returns:
            dict: A dictionary containing the path to the downloaded audio file and chapter details.
        """

        logger.info(f"Downloading audio for video: {video_url}")

        yt = YouTube(video_url)
        video = yt.streams.filter(only_audio=True).first()
        output_path = video.download(filename=f"{clean_yt_title(yt.title)}.mp4")
        logger.info(f"Downloaded full audio to {output_path}")
        return {
            "audio_path": output_path,
            "yt_video_title": clean_yt_title(yt.title),
            "chapters": [
                {
                    "title": chapter.title,
                    "start": chapter.start_seconds,
                    "end": next_chapter.start_seconds
                    if i < len(yt.chapters) - 1
                    else yt.length,
                }
                for i, (chapter, next_chapter) in enumerate(
                    zip(yt.chapters, yt.chapters[1:] + [None])
                )
            ],
        }

    @task(max_active_tis_per_dag=4)  # more than 1 exits with -9 (OOM)
    def split_audio(audio_info: dict) -> list[dict]:
        """
        Splits the audio file into segments based on the chapter details.

        Args:
            audio_info (dict): The output of the download_audio task.

        Returns:
            list[dict]: A list of dictionaries, each containing metadata for an audio segment.
        """

        logger.info(
            f"Splitting audio into segments for video: {audio_info['yt_video_title']}"
        )
        audio = AudioSegment.from_file(audio_info["audio_path"])
        segments = []

        for chapter in audio_info["chapters"]:
            title, start_time = chapter["title"], chapter["start"]
            end_time = chapter["end"]
            duration = end_time - start_time

            if title.startswith("Game ") and title[5].isdigit():
                segment_count = (duration // 300) + (1 if duration % 300 > 0 else 0)
                for j in range(segment_count):
                    seg_start = start_time + (j * 300)
                    seg_end = min(seg_start + 300, end_time)
                    filename = f"{title}_part{j+1}_{audio_info['yt_video_title']}.wav"
                    extract = audio[seg_start * 1000 : seg_end * 1000]
                    extract.export(filename, format="wav")
                    audio_metadata = mediainfo(filename)
                    segments.append(
                        get_segment_metadata(
                            audio_info,
                            f"{title} (Part {j+1})",
                            filename,
                            audio_metadata,
                        )
                    )
                    logger.info(f"Processed segment: {title} ({seg_start}-{seg_end})")
            else:
                filename = f"{title}_{audio_info['yt_video_title']}.wav"
                extract = audio[start_time * 1000 : end_time * 1000]
                extract.export(filename, format="wav")
                audio_metadata = mediainfo(filename)
                segments.append(
                    get_segment_metadata(audio_info, title, filename, audio_metadata)
                )
                logger.info(f"Processed segment: {title} ({start_time}-{end_time})")

        # clean up local file
        os.remove(audio_info["audio_path"])

        return segments

    @task(max_active_tis_per_dag=4)
    def transcribe_segments(segments: list[dict]) -> list[dict]:
        """
        Uses a Whisper model to transcribe audio segments.

        Args:
            segment (list[dict]): A list of dictionaries containing metadata for the audio segments.

        Returns:
            list[dict]: The input list with extra keys added for the transcriptions.
        """

        logger.info("Transcribing audio segments")
        whisper_model = whisper.load_model("tiny")
        enhanced_segments = []
        for segment in segments:
            logger.info(
                f"Transcribing segment: {segment['title']} ({segment['filename']})"
            )
            result = whisper_model.transcribe(segment["filename"])
            segment["text"] = result["text"]
            gpt_summary_dict = get_gpt_summary(result["text"])
            segment["gpt_clarity"] = gpt_summary_dict["clarity"]
            segment["gpt_intensity"] = gpt_summary_dict["intensity"]
            segment["gpt_summary"] = gpt_summary_dict["summary"]
            logger.info(
                f"Transcribed segment: {segment['title']} ({segment['filename']})"
            )
            enhanced_segments.append(segment)

        return enhanced_segments

    @task(max_active_tis_per_dag=4)
    def upload_to_gcs(transcription: dict) -> dict:
        """
        Uploads the transcribed audio segment to Google Cloud Storage.

        Args:
            transcription (dict): A dictionary containing metadata for the transcribed audio segment.

        Returns:
            dict: The input dictionary with the 'text' key added containing the transcription.
        """

        gcs_hook = GCSHook()
        bucket_name = "lolesports_voice_analytics_files"
        logger.info(
            f"Uploading segment: {transcription['title']} ({transcription['filename']}) to GCS"
        )
        audio_path = (
            f"audio/{transcription['yt_video_title']}/{transcription['filename']}"
        )
        gcs_hook.upload(
            bucket_name=bucket_name,
            object_name=audio_path,
            filename=transcription["filename"],
        )
        logger.info(
            f"Uploaded segment: {transcription['title']} ({transcription['filename']}) to GCS"
        )
        # clean up local file
        os.remove(transcription["filename"])

        return transcription

    @task(max_active_tis_per_dag=4)
    def upload_full_transcription_to_gcs(transcriptions: list[dict]) -> str:
        """
        Uploads the complete transcription to Google Cloud Storage

        Args:
            transcriptions (list[dict]): A list of dictionaries containing metadata for the transcribed audio segments.

        Returns:
            str: The YouTube video title used as the filename for the complete transcription.
        """

        transcriptions = list(transcriptions)  # set(transcriptions)
        # take yt video name from 1st transcription
        yt_video_title = transcriptions[0]["yt_video_title"].strip()
        yt_video_title = "".join(e for e in yt_video_title if e.isalnum())[:15]

        required_fields = set(i["name"] for i in get_raw_audio_bq_schema())
        with open("complete_transcription.json", "w") as f:
            for transcription in transcriptions:
                transcription["ingestion_timestamp"] = datetime.now().isoformat()
                if set(transcription.keys()) != required_fields:
                    logger.error(
                        f"Missing fields in transcription: {transcription}. Required fields: {required_fields}"
                    )
                    raise ValueError(
                        f"Missing fields in transcription: {transcription.keys()}. Required fields: {required_fields}"
                    )

                f.write(json.dumps(transcription) + "\n")

        combined_transcript_path = (
            f"transcriptions/{yt_video_title}/complete_transcription.json"
        )
        logger.info(
            f"Uploading complete transcription for video: {yt_video_title} to GCS: {combined_transcript_path}"
        )
        gcs_hook = GCSHook()
        gcs_hook.upload(
            bucket_name="lolesports_voice_analytics_files",
            object_name=combined_transcript_path,
            filename="complete_transcription.json",
        )
        # clean up local files
        os.remove("complete_transcription.json")

        return yt_video_title

    add_transcription_to_bq = GCSToBigQueryOperator.partial(
        task_id="add_transcription_to_bq_table",
        bucket="lolesports_voice_analytics_files",
        destination_project_dataset_table="dataengcamp-427114.lolesports_voice_analytics.raw_data_from_video",
        source_format="NEWLINE_DELIMITED_JSON",
        write_disposition="WRITE_APPEND",
        schema_fields=get_raw_audio_bq_schema(),
    ).expand(
        source_objects=[
            "transcriptions/{{task_instance.xcom_pull(task_ids='upload_full_transcription_to_gcs')}}/complete_transcription.json"
        ]
    )

    unprocessed_video_urls = check_if_videos_already_processed()
    valid_videos_urls = data_quality_check(video_urls=unprocessed_video_urls)
    downloaded_audios = download_audios.expand(video_url=valid_videos_urls)
    segments = split_audio.expand(audio_info=downloaded_audios)
    transcribed_segments = transcribe_segments.expand(segments=segments)
    uploaded_segments = upload_to_gcs.expand(transcription=transcribed_segments)
    uploaded_transcription_path = upload_full_transcription_to_gcs.expand(
        transcriptions=uploaded_segments
    )

    uploaded_transcription_path >> add_transcription_to_bq


dag = youtube_transcription()
