from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from airflow.models import BaseOperator

from hyperopt import fmin, atpe

from hyperopt.base import SONify
from hyperopt.base import JOB_STATE_DONE, JOB_STATE_ERROR, STATUS_OK, STATUS_FAIL
import time
import numpy as np
if not hasattr(np, "warnings"):
    class Dummy:
        def filterwarnings(*args, **kwargs):
            pass
    setattr(np, "warnings", Dummy())

from .mongoexp import MongoTrials, MongoCtrl, MongoJobs


def no_progress_loss(min_evals=20, iteration_stop_count=10, percent_increase=0.0):

    def stop_fn(trials):

        good_trials = [t for t in trials.trials if t["result"]["status"] == "ok"]
        good_trials.sort(key= lambda t: t.get("tid"))
        latest_losses = [t["result"]["loss"] for t in good_trials]
        
        if len(latest_losses) < min_evals:
            return False
            
        
        iteration_no_progress = len(latest_losses) - np.argmin(latest_losses)
        best_loss = np.min(latest_losses)

        return iteration_no_progress >= iteration_stop_count

    
    return stop_fn


class HyperoptTaskGroup(TaskGroup):
    def __init__(self, space, algo=atpe.suggest, max_evals=100, min_evals=20, params={},
                 group_id="optimize", mongo_connection='mongo://mongo:27017/hyperopt/jobs', 
                 params_in_dagrun=False,
                 *args, **kwargs):
        self.space = space
        self.algo = algo
        self.max_evals = max_evals
        self.min_evals = min_evals
        self.final_run = False
        self.mongo_connection = mongo_connection
        self.params_in_dagrun = params_in_dagrun
       
        

        kwargs["ui_color"] = "#4fe51d"
        kwargs["ui_fgcolor"] = "#fff"
        kwargs["group_id"] = group_id

        super().__init__(*args, **kwargs)
        
        if not self.default_args:
            self.default_args = {}
        self.default_args["params"] = params
        
        
    def reset_op(self, *args, **kwargs):

        trials = MongoTrials(self.mongo_connection, exp_key=self.dag_id + "_" + self.group_id, refresh=True)
        trials.delete_all()
            
        return True
           
        
    def optimizer_op(self, *args, **kwargs):
        dag_run = kwargs["dag_run"]
        
        self.init_task.clear(start_date=kwargs['execution_date'], end_date=kwargs['execution_date'])
        trials = MongoTrials(self.mongo_connection, exp_key=self.dag_id + "_" + self.group_id, refresh=True)

        
        def _sample(parameters):
            return {"loss": 0.0 , "status": "ok"}
        
        stop_fn = no_progress_loss(min_evals=self.min_evals)
        
        while True:
        
            new_max_evals = len(trials.trials) + 1
        

            fmin(
                algo=self.algo,
                fn=_sample,
                max_evals=new_max_evals,
                space=self.space,
                trials=trials,
                show_progressbar=False,
                timeout=1
            )
            
            trials.refresh()
            if stop_fn(trials) or len(trials.trials) != new_max_evals:
                break
                
        new_params = trials.argmin
        new_params = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k,v in new_params.items()}
        new_params["__tid"] = "final"
        
        self.default_args["params"].update(new_params)
        if self.params_in_dagrun:
            dag_run.conf = self.default_args["params"]
        
        for task in self.opti_tasks:
            task.parameters["params"] = self.default_args["params"]
            
        self.exit_task.clear(start_date=kwargs['execution_date'], end_date=kwargs['execution_date'])
        for t in self.opti_tasks:
            t.clear(start_date=kwargs['execution_date'], end_date=kwargs['execution_date'])        
            
        return trials.argmin
        


    def init_op(self, *args, **kwargs):
        
        dag_run = kwargs["dag_run"]
        exp_key = self.dag_id + "_" + self.group_id
        
        trials = MongoTrials(self.mongo_connection, exp_key=exp_key, refresh=True)
        
        mj = MongoJobs.new_from_connection_str(self.mongo_connection)
        
        job = mj.reserve("runner1", exp_key=exp_key)
        retry = 10
        while not job and retry > 0:
            time.sleep(5)
            job = mj.reserve("runner1", exp_key=exp_key)
            retry = retry - 1
        
        
        
        if job:
            new_params = job.get("misc").get("vals")
            new_params["__tid"] = job["tid"]
        else:
            new_params = trials.argmin
            new_params["__tid"] = "final"
            
        new_params = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k,v in new_params.items()}
        
    
        self.default_args["params"].update(new_params)
        if self.params_in_dagrun:
            dag_run.conf = self.default_args["params"]
        
        for task in self.opti_tasks:
            task.parameters["params"] = self.default_args["params"]
            
        self.exit_task.clear(start_date=kwargs['execution_date'], end_date=kwargs['execution_date'])
        for t in self.opti_tasks:
            t.clear(start_date=kwargs['execution_date'], end_date=kwargs['execution_date'])
        
        return self.default_args["params"]

    
    def exit_op(self, *args, **kwargs):
        dag_run = kwargs["dag_run"]
        exp_key = self.dag_id + "_" + self.group_id
        
        if self.final_run:
            return "END"
        
        
        total_loss = 0
        loss_found = False
        tid = None
        status = STATUS_FAIL
        for task in self.opti_leaves:
            return_value = task.xcom_pull(task_ids=task.task_id, key='return_value', context=kwargs)

            if return_value and "loss" in return_value:
                loss_value = return_value["loss"]
                total_loss += loss_value
                loss_found = True
                if "__tid" in return_value:
                    tid = return_value["__tid"]
                if "status" in return_value:
                    status = return_value["status"]                 
    
        if not loss_found:
            total_loss = None
            
        trials = MongoTrials(self.mongo_connection, exp_key=exp_key, refresh=True)
        mj = MongoJobs.new_from_connection_str(self.mongo_connection)
        
        jobs_running = mj.jobs_running()
        
        if tid == "final":
            # if len(jobs_running) > 0:
            #     self.init_task.clear(start_date=kwargs['execution_date'], end_date=kwargs['execution_date'])
            return "END"
        
        
        if len(jobs_running) == 0:
            job = jobs_running[0]
        else:
            if not tid:
                raise Exception("No tid defined")
            job = [j for j in jobs_running if j["tid"] == tid][0]
            
        result = SONify({"loss": total_loss, "status": status})
        ctrl = MongoCtrl(
                trials=trials,
                read_only=False,
                current_trial=job)
        ctrl.checkpoint(result)
        mj.update(job, {'state': JOB_STATE_DONE})
        
        self.init_task.clear(start_date=kwargs['execution_date'], end_date=kwargs['execution_date'])
           
        return total_loss
        
        
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
        
        
        self.reset_task = PythonOperator(
            task_id="reset",
            python_callable=self.reset_op,
            trigger_rule="all_success",
            task_group=self,
            dag=self.dag,
            provide_context=True,
        ) 
        
        self.optimizer_task = PythonOperator(
            task_id="optimizer",
            python_callable=self.optimizer_op,
            trigger_rule="all_success",
            task_group=self,
            dag=self.dag,
            provide_context=True,
        )              
        
        self.init_task = PythonOperator(
            task_id="init",
            python_callable=self.init_op,
            trigger_rule="all_success",
            task_group=self,
            dag=self.dag,
            provide_context=True,
        )
        
        self.reset_task >> self.optimizer_task
        self.reset_task >> self.init_task
        
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
        
        
