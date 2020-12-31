import json
import requests
import base64
import os
import time


class _DatabricksIFrame(object):
    """
    Class to embed a databricks run result in an iframe in an IPython notebook
    """

    iframe = """
        <iframe
            width="100%"
            height="600px"
            src="{data}"
            frameborder="0"
            allowfullscreen
            sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
        ></iframe>
        """

    def __init__(self, data, **kwargs):
        import base64
        encoded_string = base64.b64encode(bytes(data, 'utf-8')).decode('utf-8')
        self.src = "data:text/html;base64,"+encoded_string

    def _repr_html_(self):
        """return the embed iframe"""
        return self.iframe.format(data=self.src)


class Databricks:
    """
    A interface class to controll Databricks remotely via the 2.0 api
    For more information see https://docs.databricks.com/dev-tools/api/2.0/index.html
    """

    def __init__(self):
        import configparser
        import mlflow
        from mlflow.tracking.client import MlflowClient

        config = configparser.ConfigParser()
        config.read('/defaults.cfg')

        # load important parameters from config
        self.token = config["Databricks"]["TOKEN"]
        self.registry = config["Databricks"]["REGISTRY"]
        self.user = config["Databricks"]["USER"]

        # initilaize mlflow connection
        os.environ["MLFLOW_TRACKING_TOKEN"] = self.token
        mlflow.set_tracking_uri(self.registry)
        mlflow.set_registry_uri(self.registry)
        self.mlflow = MlflowClient()

    def _databricks_post(self, action, body):
        """
        A helper function to make the databricks API post request, request/response is encoded/decoded as JSON
        """
        response = requests.post(
            self.registry + action,
            headers={'Authorization': 'Bearer %s' % self.token},
            json=body
        )
        return response.json()

    def _databricks_get(self, action):
        """
        A helper function to make the databricks API get request, request/response is encoded/decoded as JSON
        """
        response = requests.get(
            self.registry + action,
            headers={'Authorization': 'Bearer %s' % self.token}
        )
        return response.json()

    def _get_job_config(self, name, fullPath, new_cluster=None, existing_cluster_id=None, libraries=None):
        """
        Create a default job configuration
        """
        # create the default
        output = {
            "name": name,
            "email_notifications": {
                "on_start": [],
                "on_success": [],
                "on_failure": [self.user]
            },
            "notebook_task": {
                "notebook_path": fullPath
            }
        }

        # append the cluster configuration
        if new_cluster:
            output["new_cluster"] = new_cluster
        elif existing_cluster_id:
            output["existing_cluster_id"] = existing_cluster_id
        else:
            raise Exception("No cluster defined")

        if libraries:
            output["libraries"] = libraries

        return output

    def _get_fullpath(self, fileName):
        """
        Helper to cumpute the target filename of noteobooks
        """
        return os.path.join("/Users/", self.user, fileName)

    def upload_file(self, localFile, targetFile=None):
        """
        Upload a data file to the FileStore

        If targetFile is not defined and the localFile is located in
        the FileStore, this file is used for the upload.
        """

        if not targetFile:
            checkLocalFile = os.path.join(
                "/home/af-hub/workflow/FileStore", localFile)
            if os.path.isfile(checkLocalFile):
                targetFile = localFile
                localFile = checkLocalFile
            else:
                raise Exception("File {} not found at {}. Please specify a targetFile or you can only use files in the local FileStore".format(
                    localFile, checkLocalFile))

        fullPath = os.path.join(
            "/FileStore/shared_uploads", self.user, targetFile)
        print("upload {} => {}".format(localFile, fullPath))

        # Create a handle that will be used to add blocks
        res = self._databricks_post(
            "/api/2.0/dbfs/create", {"path": fullPath, "overwrite": "true"})

        if "error_code" in res:
            raise Exception(res)

        handle = res['handle']

        # add data in chunks
        with open(localFile, "rb") as f:
            while True:
                # A block can be at most 1MB
                block = f.read(1 << 20)
                if not block:
                    break
                data = base64.standard_b64encode(block).decode("utf-8")
                res = self._databricks_post(
                    "/api/2.0/dbfs/add-block", {"handle": handle, "data": data})

                if "error_code" in res:
                    raise Exception(res)

        # close handle
        res = self._databricks_post("/api/2.0/dbfs/close", {"handle": handle})

        if "error_code" in res:
            raise Exception(res)

    def file_info(self, remoteFile):
        """
        Get the file information of a file or directory. If the file or directory does not exist,
        this call throws an exception with RESOURCE_DOES_NOT_EXIST
        """
        fullPath = os.path.join(
            "/FileStore/shared_uploads", self.user, remoteFile)

        # Get the file info
        res = self._databricks_get(
            "/api/2.0/dbfs/get-status?path={}".format(fullPath))

        if "error_code" in res:
            raise Exception(res)

        return res

    def download_file(self, remoteFile, targetFile=None):
        """
        Return the contents of a file.

        If the file does not exist, this call throws an exception with RESOURCE_DOES_NOT_EXIST.
        If the path is a directory, the read length is negative, or if the offset is negative,
        this call throws an exception with INVALID_PARAMETER_VALUE

        If no targetFile is chosen the file is placed in the local FileStore
        """

        # if targetFile is empty, copy the file into the local FileStore
        if not targetFile:
            targetFile = os.path.join(
                "/home/af-hub/workflow/FileStore", remoteFile)
            targetDir = os.path.dirname(targetFile)
            # create folder if needed
            if not os.path.isdir(targetDir):
                os.makedirs(targetDir)

        # get the full path in dbfs
        fullPath = os.path.join(
            "/FileStore/shared_uploads", self.user, remoteFile)

        print("download {} => {}".format(fullPath, targetFile))

        # get the file info to extract the length of the file
        file_info = self.file_info(remoteFile)

        total_read = 0
        with open(targetFile, "wb") as f:
            while total_read < file_info["file_size"]:
                data = self._databricks_get(
                    "/api/2.0/dbfs/read?path={}&offset={}".format(fullPath, total_read))

                if "error_code" in data:
                    raise Exception(data)

                total_read += data["bytes_read"]

                f.write(base64.b64decode(data["data"]))

    def import_ipynb(self, localFile, targetFile):
        """
        Import a jupyter notebook to databricks
        """
        fullPath = self._get_fullpath(targetFile)
        print("import {} => {}".format(localFile, fullPath))

        with open(localFile, "rb") as f:
            block = f.read()
            data = base64.standard_b64encode(block).decode("utf-8")

            res = self._databricks_post("/api/2.0/workspace/import",
                                        {"format": "JUPYTER",
                                         "path": fullPath,
                                         "overwrite": True,
                                         "content": data})

        if "error_code" in res:
            raise Exception(res)

    def import_py(self, localFile, targetFile):
        """
        Import a plain python file into databricks
        """
        fullPath = self._get_fullpath(targetFile)
        print("import {} => {}".format(localFile, fullPath))

        with open(localFile, "rb") as f:
            block = f.read()
            data = base64.standard_b64encode(block).decode("utf-8")

            res = self._databricks_post("/api/2.0/workspace/import",
                                        {"format": "SOURCE",
                                         "language": "PYTHON",
                                         "path": fullPath,
                                         "overwrite": True,
                                         "content": data})

        if "error_code" in res:
            raise Exception(res)

    def mkdirs(self, folder):
        """
        Create the given directory and necessary parent directories if they do not exists.
        """
        fullPath = self._get_fullpath(folder)
        print("mkdir {}".format(fullPath))
        res = self._databricks_post(
            "/api/2.0/workspace/mkdirs", {"path": fullPath})

        if "error_code" in res:
            raise Exception(res)

    def list_jobs(self, all=False):
        """
        List all jobs.
        """
        res = self._databricks_get("/api/2.0/jobs/list")

        if "jobs" in res:
            if all:
                return res["jobs"]
            else:
                return [el for el in res["jobs"] if el["creator_user_name"] == self.user]
        else:
            raise Exception(res)

    def delete_job(self, job_id):
        """
        Delete the job.
        """
        res = self._databricks_post("/api/2.0/jobs/delete", {"job_id": job_id})

        if "error_code" in res:
            raise Exception(res)

    def create_job(self, name, targetFile, new_cluster=None, existing_cluster_id=None, libraries=None):
        """
        Create a new job.
        """
        fullPath = self._get_fullpath(targetFile)

        # create the job configuration
        new_job = self._get_job_config(
            name, fullPath, new_cluster=new_cluster,
            existing_cluster_id=existing_cluster_id,
            libraries=libraries)

        res = self._databricks_post("/api/2.0/jobs/create", new_job)

        if "error_code" in res:
            raise Exception(res)
        return res

    def assure_job(self, name, targetFile, new_cluster=None, existing_cluster_id=None, libraries=None):
        """
        Create or update a job setting. The job is selected based on the target file
        """
        fullPath = self._get_fullpath(targetFile)

        # check existing jobs
        jobs = [el for el in self.list_jobs() if "settings" in el and "notebook_task" in el["settings"]
                and "notebook_path" in el["settings"]["notebook_task"]
                and el["settings"]["notebook_task"]["notebook_path"] == fullPath]

        if len(jobs) > 1:
            raise Exception(
                "Too many jobs based on notebook {}".format(fullPath))

        # create the job configuration
        new_job = self._get_job_config(
            name, fullPath, new_cluster=new_cluster,
            existing_cluster_id=existing_cluster_id,
            libraries=libraries)

        # create or update the job
        if len(jobs) == 0:
            res = self._databricks_post("/api/2.0/jobs/create", new_job)
        else:
            res = self._databricks_post(
                "/api/2.0/jobs/reset", {"job_id": jobs[0]["job_id"], "new_settings": new_job})
            if not "job_id" in res:
                res["job_id"] = jobs[0]["job_id"]

        if "error_code" in res:
            raise Exception(res)
        return res

    def run_job(self, job_id, params={}):
        """
        Run a job now and return the run_id of the triggered run.
        """
        res = self._databricks_post(
            "/api/2.0/jobs/run-now", {"job_id": job_id, "notebook_params": params})

        if "error_code" in res:
            raise Exception(res)

        return res

    def run_status(self, run_id):
        """
        Retrieve the metadata of a run.
        """
        res = self._databricks_get(
            "/api/2.0/jobs/runs/get?run_id={}".format(run_id))

        if "error_code" in res:
            raise Exception(res)

        return res

    def run_export(self, run_id, fileName):
        """
        Retrieve the job run task and export the HTML file.
        """
        res = self._databricks_get(
            "/api/2.0/jobs/runs/export?run_id={}".format(run_id))

        if "error_code" in res:
            raise Exception(res)

        if "views" in res:
            count = 1
            for d in res["views"]:
                with open("{}.{}.html".format(fileName.replace(".html", "").replace(".htm", ""), count), "w") as f:
                    f.write(d["content"])
            count += 1

    def run_display(self, run_id):
        from IPython.core.display import display, HTML
        """
        Retrieve the job run task and display the result.
        """
        res = self._databricks_get(
            "/api/2.0/jobs/runs/export?run_id={}".format(run_id))

        if "error_code" in res:
            raise Exception(res)

        if "views" in res:
            for d in res["views"]:
                display(HTML("<H3>{} - {}</H3>".format(d["name"], d["type"])))
                display(_DatabricksIFrame(d["content"]))

    def await_run(self, run_id, delay=120):
        """
        Wait until the job with run_id is finished
        """

        res = self.run_status(run_id)

        while (not "state" in res) or (not "life_cycle_state" in res["state"]) or (res["state"]["life_cycle_state"] != "TERMINATED"):
            time.sleep(delay)
            res = self.run_status(run_id)

        return res


    def terminate_cluster(self, existing_cluster_id):
        """
        Stop a job cluster
        """

        res = self._databricks_post("/api/2.0/clusters/delete", {"cluster_id": existing_cluster_id})

        return res