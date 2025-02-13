from airflow.decorators import dag, task
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from datetime import datetime, timedelta
from pytubefix import YouTube
from pydub import AudioSegment
from pydub.utils import mediainfo
import whisper
import json

@dag(
    dag_id="youtube_transcription_dag",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2024, 2, 13),
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    schedule_interval=None,
    catchup=False,
)
def youtube_transcription():

    @task
    def download_audio() -> dict:
        """
        Fetches a YouTube video from the given URL, downloads its audio as an MP4 file, 
        and extracts chapter details including title, start time, and end time.

        Returns:
            dict: A dictionary containing the path to the downloaded audio file and chapter details.
        """
        yt = YouTube("https://youtu.be/CwBuJgJ5b80")
        video = yt.streams.filter(only_audio=True).first()
        output_path = video.download(filename="audio.mp4")
        return {
            "audio_path": output_path,
            "yt_video_title": yt.title,
            "chapters": [
                {
                    "title": chapter.title,
                    "start": chapter.start_seconds,
                    "end": next_chapter.start_seconds if i < len(yt.chapters) - 1 else yt.length
                }
                for i, (chapter, next_chapter) in enumerate(
                    zip(yt.chapters, yt.chapters[1:] + [None])
                )
            ]
        }

    @task
    def split_audio(audio_info: dict) -> list[dict]:
        """
        Splits the audio file into segments based on the chapter details.

        Args:
            audio_info (dict): The output of the download_audio task.

        Returns:
            list[dict]: A list of dictionaries, each containing metadata for an audio segment.
        """
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
                    segments.append({
                        'yt_video_title': audio_info['yt_video_title'],
                        'title': f"{title} (Part {j+1})",
                        'filename': filename,
                        'format_name': audio_metadata['format_name'],
                        'sample_rate': audio_metadata['sample_rate'],
                        'channels': audio_metadata['channels'],
                        'bits_per_sample': audio_metadata['bits_per_sample'],
                        'duration': audio_metadata['duration'],
                        'bit_rate': audio_metadata['bit_rate'],
                        'size': audio_metadata['size'],
                        'codec_name': audio_metadata['codec_name'],
                        'min_speakers': 5,
                        'max_speakers': 5,
                        'team': 'Los Ratones' # TODO: need to make dynamic to scale. Good for now
                    })
            else:
                filename = f"{title}_{audio_info['yt_video_title']}.wav"
                extract = audio[start_time * 1000 : end_time * 1000]
                extract.export(filename, format="wav")
                audio_metadata = mediainfo(filename)
                segments.append({
                    'yt_video_title': audio_info['yt_video_title'],
                    'title': title,
                    'filename': filename,
                    'format_name': audio_metadata['format_name'],
                    'sample_rate': audio_metadata['sample_rate'],
                    'channels': audio_metadata['channels'],
                    'bits_per_sample': audio_metadata['bits_per_sample'],
                    'duration': audio_metadata['duration'],
                    'bit_rate': audio_metadata['bit_rate'],
                    'size': audio_metadata['size'],
                    'codec_name': audio_metadata['codec_name'],
                    'min_speakers': 5,
                    'max_speakers': -1,
                    'team': 'Los Ratones' # TODO: need to make dynamic to scale. Good for now
                })

        return segments

    @task(max_active_tis_per_dag=4)
    def transcribe_segment(segment: dict) -> dict:
        """
        Uses a Whisper model to transcribe an audio segment.

        Args:
            segment (dict): A dictionary containing metadata for the audio segment.

        Returns:
            dict: The input dictionary with the 'text' key added containing the transcription.
        """

        whisper_model = whisper.load_model("tiny")
        result = whisper_model.transcribe(segment['filename'])
        segment['text'] = result['text']

        return segment

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
        
        audio_path = f"audio/{transcription['yt_video_title']}/{transcription['filename']}"
        gcs_hook.upload(
            bucket_name=bucket_name,
            object_name=audio_path,
            filename=transcription['filename']
        )
        
        return transcription

    @task
    def upload_full_transcription_to_gcs(transcriptions: list[dict]) -> str:
        """
        Uploads the complete transcription to Google Cloud Storage

        Args:
            transcriptions (list[dict]): A list of dictionaries containing metadata for the transcribed audio segments.

        Returns:
            str: The YouTube video title used as the filename for the complete transcription.
        """
        # transcriptions = list(transcriptions)
        # take yt video name from 1st transcription
        yt_video_title = transcriptions[0]['yt_video_title'].strip()
        yt_video_title = "".join(e for e in yt_video_title if e.isalnum())[:15]
        with open("complete_transcription.json", "w") as f:
            for transcription in transcriptions:
                f.write(json.dumps(transcription) + "\n")
        
        gcs_hook = GCSHook()
        gcs_hook.upload(
            bucket_name="lolesports_voice_analytics_files",
            object_name=f"transcriptions/{yt_video_title}/complete_transcription.json",
            filename="complete_transcription.json"
        )
        return yt_video_title

    audio_info = download_audio()
    segments = split_audio(audio_info)

    # run transcription and upload to GCS in parallel
    transcribed_segments = transcribe_segment.expand(segment=segments)
    uploaded_segments = upload_to_gcs.expand(transcription=transcribed_segments)

    uploaded_transcription_path = upload_full_transcription_to_gcs(uploaded_segments)
    
    add_transcription_to_bq = GCSToBigQueryOperator(
        task_id="add_transcription_to_bq_table",
        bucket="randomname1234",
        source_objects=["transcriptions/{{ ti.xcom_pull(task_ids='upload_full_transcription_to_gcs') }}/complete_transcription.json"],
        destination_project_dataset_table="dataengcamp-427114.lolesports_voice_analytics.raw_data_from_video",
        source_format="NEWLINE_DELIMITED_JSON",
        write_disposition="WRITE_APPEND", 
        schema_fields=[
            {"name": "ingestion_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Timestamp of when the data was ingested", "defaultValueExpression": "CURRENT_TIMESTAMP()"},
            {"name": "yt_video_title", "type": "STRING", "mode": "NULLABLE", "description": "Title of the YouTube video"},
            {"name": "title", "type": "STRING", "mode": "NULLABLE", "description": "Title of the segment"},
            {"name": "filename", "type": "STRING", "mode": "NULLABLE", "description": "Filename of the audio segment"},
            {"name": "format_name", "type": "STRING", "mode": "NULLABLE", "description": "Format of the audio segment"},
            {"name": "sample_rate", "type": "INTEGER", "mode": "NULLABLE", "description": "Sample rate of the audio segment"},
            {"name": "channels", "type": "INTEGER", "mode": "NULLABLE", "description": "Number of channels in the audio segment"},
            {"name": "bits_per_sample", "type": "INTEGER", "mode": "NULLABLE", "description": "Bits per sample in the audio segment"},
            {"name": "duration", "type": "FLOAT", "mode": "NULLABLE", "description": "Duration of the audio segment"},
            {"name": "bit_rate", "type": "INTEGER", "mode": "NULLABLE", "description": "Bit rate of the audio segment"},
            {"name": "size", "type": "INTEGER", "mode": "NULLABLE", "description": "Size of the audio segment"},
            {"name": "codec_name", "type": "STRING", "mode": "NULLABLE", "description": "Codec name of the audio segment"},
            {"name": "min_speakers", "type": "INTEGER", "mode": "NULLABLE", "description": "Minimum number of speakers in the audio segment"},
            {"name": "max_speakers", "type": "INTEGER", "mode": "NULLABLE", "description": "Maximum number of speakers in the audio segment"},
            {"name": "team", "type": "STRING", "mode": "NULLABLE", "description": "Team name"},
            {"name": "text", "type": "STRING", "mode": "NULLABLE", "description": "Transcription of the audio segment", "defaultValueExpression": "Empty"}
        ]
    )

    uploaded_transcription_path >> add_transcription_to_bq

dag = youtube_transcription()