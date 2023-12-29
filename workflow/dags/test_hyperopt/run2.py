from airflow import utils
from airflow import DAG
from afhub.airflow import PapermillOperator, PapermillOperatorK8s, LibraryOperator
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator


# import the logging module
import logging

# get the airflow.task logger
task_logger = logging.getLogger("airflow.task")



default_args = {
    'owner': 'airflow',
    'depends_on_past': True,
    'start_date':  datetime(2020, 4, 1),
}

dag = DAG('test2', schedule_interval=None, default_args=default_args, catchup=False)




import numpy as np
if not hasattr(np, "warnings"):
    class Dummy:
        def filterwarnings(*args, **kwargs):
            pass
    setattr(np, "warnings", Dummy())



from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from airflow.models import BaseOperator
from hyperopt import fmin, tpe, Trials, hp, FMinIter
from hyperopt import atpe
from hyperopt import Domain
from hyperopt.early_stop import no_progress_loss

class HyperoptTaskGroup(TaskGroup):
    def __init__(self, space, algo=atpe.suggest, max_evals=100, min_evals=20, early_stopping=True, params={}, *args, **kwargs):
        self.space = space
        self.algo = algo
        self.max_evals = max_evals
        self.min_evals = min_evals
        
        self.trials = Trials()

        kwargs["ui_color"] = "#4fe51d"
        kwargs["ui_fgcolor"] = "#fff"

        super().__init__(*args, **kwargs)
        
        if not self.default_args:
            self.default_args = {}
        self.default_args["params"] = params
            
        
        
            
        
      
        
    def get_new_params(self):
        def _sample(parameters):
            return {"loss": 0.0 , "status": "ok"}
        
        new_max_evals = len(self.trials.trials) + 1
        
        if len(self.trials.trials) < self.min_evals - 10:
            fmin(
                algo=self.algo,
                fn=_sample,
                max_evals=new_max_evals,
                space=self.space,
                trials=self.trials,
                show_progressbar=False
            )
        else:
            fmin(
                algo=self.algo,
                fn=_sample,
                max_evals=new_max_evals,
                space=self.space,
                trials=self.trials,
                early_stop_fn=no_progress_loss(10, percent_increase=.1),
                show_progressbar=False
            )
        if len(self.trials) == new_max_evals:
            res = self.trials.trials[-1]['misc']['vals']
            return {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k,v in res.items()}
        else:
            return None
        
        

    def init_op(self, *args, **kwargs):
        task_logger.critical("init")
        
        dag_run = kwargs["dag_run"]
        
        
        
        
        
        
        new_params = self.get_new_params()
        self.default_args["params"].update(new_params)
        
        
        for task in self.opti_tasks:
            task.parameters["params"] = self.default_args["params"]
            dag_run.conf = self.default_args["params"]
            task_logger.critical(task)
            task_logger.critical(task.parameters)
            
        
        return self.default_args["params"]
        
        
    def exit_op(self, *args, **kwargs):
        pass
        
        
    def add(self, task: BaseOperator) -> None:
        super(HyperoptTaskGroup, self).add(task)   
        
        
            
            

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, _type, _value, _tb):
        
        super().__exit__(_type, _value, _tb)
        
        self.opti_roots = list(self.get_roots())
        self.opti_leaves = list(self.get_leaves())
        self.opti_tasks = list(self.children.values())
        
        self.init_task = PythonOperator(
            task_id="init",
            python_callable=self.init_op,
            trigger_rule="all_success",
            task_group=self,
            dag=self.dag,
            provide_context=True,
        )

        
        self.exit_task = PythonOperator(
            task_id="exit",
            python_callable=self.exit_op,
            trigger_rule="all_success",
            task_group=self,
            dag=self.dag,
            provide_context=True,
        )        
        

        for task in self.opti_roots:
            task.set_upstream(self.init_task)
        for task in self.opti_leaves:
            task.set_downstream(self.exit_task)
        
        

            
        
        
        
with HyperoptTaskGroup(
    space=hp.uniform('x', -10, 10),
    params={"t": 12},
    group_id="optimize",
    dag=dag) as opti:
    

    a = PapermillOperator(
        task_id="run_a",
        inputFile="test.ipynb",
        outputFile="local.ipynb",

        parameters={"filename": "PapermillOperator"},

        dag=dag
    )
    
    b = PapermillOperator(
        task_id="rub_b",
        inputFile="test.ipynb",
        outputFile="local.ipynb",

        parameters={"filename": "PapermillOperator"},

        dag=dag
    )
    
    a >> b

        