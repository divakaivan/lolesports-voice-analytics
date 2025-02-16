from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from datetime import datetime, timedelta
from include.utils import scrape_team_data

with DAG(
    dag_id="lol_team_scraper",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "start_date": datetime(2024, 2, 14),
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
    },
    description="Scrapes LoL team member data from Fandom wiki",
    schedule_interval=None,
    catchup=False,
    tags=["ivan", "lol", "team_scraping"],
) as dag:
    scrape_task = PythonOperator(
        task_id="scrape_team_data",
        python_callable=scrape_team_data,
        op_kwargs={"team_name": "Los Ratones"},
    )

    insert_task = BigQueryInsertJobOperator(
        task_id="insert_team_data",
        configuration={"query": {"query": scrape_task.output, "useLegacySql": False}},
    )

    scrape_task >> insert_task
