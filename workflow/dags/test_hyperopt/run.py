from airflow import utils
from airflow import DAG
from afhub.airflow import PapermillOperator, PapermillOperatorK8s, LibraryOperator
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator


default_args = {
    'owner': 'airflow',
    'depends_on_past': True,
    'start_date':  datetime(2020, 4, 1),
}

dag = DAG('K8S', schedule_interval=None, default_args=default_args, catchup=False)



from airflow.utils.task_group import TaskGroup
from hyperopt import fmin, tpe, Trials, hp

class HyperoptTaskGroup(TaskGroup):
    def __init__(self, space, algo=tpe.suggest, max_evals=5, *args, **kwargs):
        self.space = space
        self.algo = algo
        self.max_evals = max_evals

        kwargs["ui_color"] = "#1d9ce5"
        kwargs["ui_fgcolor"] = "#fff"

        super().__init__(*args, **kwargs)

    def run_optimization(self, context):
        self.log.info("Running optimization")
        trials = Trials()
        
        def objective_wrapper(params):
            self.log.info("params: %s", params)
            self.log.info("context: %s", context)
            # Execute the TaskGroup and get the output of the last operator
            super().execute(context)
            loss_value = context['ti'].xcom_pull(task_ids=self.group_id, key='task_instance_result')
            return loss_value

        best = fmin(
            fn=objective_wrapper,
            space=self.space,
            algo=self.algo,
            max_evals=self.max_evals,
            trials=trials
        )

        optimization_result = {'best_params': best, 'best_result': trials.best_trial['result']}
        return optimization_result

    def execute(self, context):
        self.ti = context['ti']
        self.ti.pid = None        
        self.log.info("Executing HyperoptTaskGroup")
        result = self.run_optimization(context)
        self.xcom_push(context, 'optimization_result', result)

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, _type, _value, _tb):
        super().__exit__(_type, _value, _tb)


        
with HyperoptTaskGroup(
    space=hp.uniform('x', -10, 10),
    group_id="optimize",
    dag=dag) as opti:
    

    l = PapermillOperator(
        task_id="local_run",
        inputFile="test.ipynb",
        outputFile="local.ipynb",

        parameters={"filename": "PapermillOperator"},

        dag=dag
    )

