import os
import requests
import psycopg2
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables (.env debe estar montado en el contenedor o pasado por variables***)
load_dotenv('.env')

PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://192.168.3.155:9090/api/v1/query')
UNIVERSAL_QUERY = '{__name__=~".+"}'

DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST', '192.168.3.155'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def extract_and_load():
    print(f"[{datetime.now()}] Iniciando extracción masiva desde {PROMETHEUS_URL}...")
    response = requests.get(PROMETHEUS_URL, params={'query': UNIVERSAL_QUERY})
    response.raise_for_status()
    data = response.json()['data']['result']
    
    print(f"Conectando a BD. Procesando {len(data)} métricas...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO raw_telemetry (time, metric_name, labels, value)
        VALUES (%s, %s, %s, %s)
    """

    count = 0
    for item in data:
        time_obj = datetime.fromtimestamp(item['value'][0])
        try:
            value = float(item['value'][1])
        except ValueError:
            value = 0.0

        metric_dict = item['metric']
        metric_name = metric_dict.pop('__name__', 'unnamed')
        labels = json.dumps(metric_dict)

        cursor.execute(insert_query, (time_obj, metric_name, labels, value))
        count += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"[{datetime.now()}] Éxito: {count} registros insertados en TimescaleDB.")

if __name__ == "__main__":
    # Al estar en Docker, este script corre directamente
    try:
        extract_and_load()
    except (requests.exceptions.ConnectionError, psycopg2.OperationalError) as e:
        print(f"💤 Servidor apagado o servicios no listos. Detalle: {e}")
        print("✅ Saliendo pacíficamente (Exit 0) para evitar falsas alarmas en Airflow.")
        sys.exit(0)