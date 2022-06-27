from airflow import utils
from airflow import DAG
from afhub.airflow import PapermillOperator, PapermillOperatorK8s, LibraryOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'airflow',
    'depends_on_past': True,
    'start_date':  datetime(2020, 4, 1),
}

dag = DAG('K8S', schedule_interval=None, default_args=default_args, catchup=False)


lib_task = LibraryOperator(
    task_id="build_lib",
    libFolder="testlib",
    dag=dag,
    to_databricks=False
)


k = PapermillOperatorK8s(
    task_id="k8s_run",
    inputFile="test.ipynb",
    outputFile="k8s.ipynb",
    
    labels={"foo": "bar"},
    parameters={"filename": "PapermillOperatorK8s"},

    dag=dag
)


l = PapermillOperator(
    task_id="local_run",
    inputFile="test.ipynb",
    outputFile="local.ipynb",
    
    parameters={"filename": "PapermillOperator"},

    dag=dag
)


lib_task >> k >> l
