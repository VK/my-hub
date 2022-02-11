from airflow import utils
from airflow import DAG
from afhub.airflow import PapermillOperator, UploadToDatabricks, DatabricksOperator, DownloadFromDatabricks, LibraryOperator, RetryTaskGroup
from datetime import datetime, timedelta


default_args = {
    'owner': 'airflow',
    'depends_on_past': True,
    'start_date':  datetime(2020, 4, 1),
}

dag = DAG('TestOperator', schedule_interval=None, default_args=default_args, catchup=False)



lib_task = LibraryOperator(
    task_id="build_lib",
    libFolder="testlib",
    outputFolder="test",
    dag=dag
)


t1 = PapermillOperator(
    task_id="create_file",
    inputFile="01_CreateFile.ipynb",
    outputFile="test/01_CreateFile.ipynb",
    parameters={"a": 100},
    dag=dag
)

lib_task >> t1

with RetryTaskGroup("upload_and_open", dag=dag) as gr1:

    t2 = UploadToDatabricks(
        task_id="upload_to_dbr",
        inputFile="test/test.json",
        dag=dag
    )

    t3 = DatabricksOperator(
        task_id="open_file",
        inputFile="03_OpenFile.ipynb",
        outputFile="test/03_OpenFile.ipynb",
        parameters={"d": 1234},
        dag=dag,
        existing_cluster_id = "1001-122108-fife94",
        terminate_cluster = True
    )
    #t3.add_library(lib_task)
    t2 >> t3

t1 >> gr1



t4 = DownloadFromDatabricks(
    task_id="download_from_dbr",
    inputFile="test/test_output.json",
    dag=dag
)

t3 >> t4