from airflow import utils
from airflow import DAG
from afhub.airflow import PapermillOperator,  HyperoptTaskGroup
from datetime import datetime


from hyperopt import hp

default_args = {
    'owner': 'airflow',
    'depends_on_past': True,
    'start_date':  datetime(2020, 4, 1),
}

dag = DAG('hyperopt', schedule_interval=None, default_args=default_args, catchup=False)



with HyperoptTaskGroup(
    space=hp.uniform('x', -10, 10),
    params={"t": 12},
    group_id="optimize",
    dag=dag) as opti:
    

    b = PapermillOperator(
        task_id="opti_task",
        inputFile="opti_task.ipynb",
        outputFile="opti_task.ipynb",

        parameters={"filename": "PapermillOperator"},

        dag=dag
    )
    


a = PapermillOperator(
    task_id="init_task",
    inputFile="init_task.ipynb",
    outputFile="init_task.ipynb",
    dag=dag
)

c = PapermillOperator(
    task_id="end_task",
    inputFile="end_task.ipynb",
    outputFile="end_task.ipynb",
    dag=dag
)


a  >> opti >> c