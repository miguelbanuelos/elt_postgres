from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'prometheus_to_timescale_docker_elt',
    default_args=default_args,
    description='Extract telemetry data from Prometheus and load it into TimescaleDB using Docker',
    schedule_interval='0 * * * *', # Expresión CRON: Al minuto 0 de cada hora
    catchup=False,
    tags=['telemetry', 'elt', 'docker'],
) as dag:

    # -------------------------------------------------------------
    # DOCKER OPERATOR
    # -------------------------------------------------------------
    run_etl_task = DockerOperator(
        task_id='extract_and_load_telemetry_container',
        
        image='elt_postgres_telemetry:latest',
        container_name='task_elt_postgres',
        api_version='auto',
        
        # autoremove container
        auto_remove=True,
        
        # execute the ELT script inside the container
        command="python elt.py",
        
        # Connect container to the network
        network_mode="shared_network", 
        
        
        mounts=[
            Mount(source="/docker/elt_postgres/.env", target="/app/.env", type="bind")
        ],
        
        # allow docker create the container with root privileges
        docker_url="unix://var/run/docker.sock"
    )

    run_etl_task