from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 14),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def scrape_team_data(team_name):
    url = f"https://lol.fandom.com/wiki/{team_name}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    table = soup.find('table', {'class': 'wikitable'})
    
    if table is None:
        raise ValueError(f"Could not find team members table for {team_name}")
    
    rows = []
    for tr in table.find_all('tr')[1:]:
        cols = tr.find_all(['td', 'th'])
        if len(cols) >= 4:
            name_cell = cols[2].text.strip().replace("'", "\\'")
            team_cell = team_name.replace("'", "\\'")
            rows.append(f"STRUCT('{name_cell}' as player_name, '{team_cell}' as team, "
                       f"CURRENT_DATE() as effective_start_date, CAST(NULL AS DATE) as effective_end_date, "
                       f"TRUE as is_current, CURRENT_TIMESTAMP() as created_at, "
                       f"CURRENT_TIMESTAMP() as updated_at)")

    values = ',\n                '.join(rows)

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

    print(sql_query)
    return sql_query

with DAG(
    'lol_team_scraper',
    default_args=default_args,
    description='Scrapes LoL team member data from Fandom wiki',
    schedule_interval=None,
    catchup=False
) as dag:

    scrape_task = PythonOperator(
        task_id='scrape_team_data',
        python_callable=scrape_team_data,
        op_kwargs={'team_name': 'Los Ratones'},
    )

    insert_task = BigQueryInsertJobOperator(
        task_id='insert_team_data',
        configuration={
            'query': {
                'query': scrape_task.output,
                'useLegacySql': False
            }
        }
    )

    scrape_task >> insert_task
