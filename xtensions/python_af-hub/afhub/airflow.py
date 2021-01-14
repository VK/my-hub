from . import databricks
from airflow.exceptions import AirflowException
from airflow.models import BaseOperator, SkipMixin
from airflow.utils.decorators import apply_defaults
from airflow.utils.file import TemporaryDirectory
from airflow.utils.operator_helpers import context_to_airflow_vars
import papermill as pm
import os
import smtplib
import json

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import textwrap


# import config file
import configparser
config = configparser.ConfigParser()
config.read('/defaults.cfg')


class PapermillOperator(BaseOperator):
    """

    Executes a Jupyter Notebook with papermill locally.

    Attributes
    ----------
    inputFile : str
        the input Jupyter Notebook
    outputFile : str
        the output Jupyter Notebook
    parameters : dict
        additional parameters for the run
    """
    template_fields = ('templates_dict',)
    template_ext = tuple()
    ui_color = '#ffcca9'

    # since we won't mutate the arguments, we should just do the shallow copy
    # there are some cases we can't deepcopy the objects(e.g protobuf).
    shallow_copy_attrs = ('python_callable', 'op_kwargs',)

    @apply_defaults
    def __init__(
            self,
            inputFile,
            outputFile,
            parameters=None,
            op_args=None,
            op_kwargs=None,
            # provide_context=False,
            templates_dict=None,
            templates_exts=None,
            *args, **kwargs):
        super(PapermillOperator, self).__init__(*args, **kwargs)
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}
        #self.provide_context = provide_context
        self.templates_dict = templates_dict
        if templates_exts:
            self.template_ext = templates_exts
        self.inputFile = inputFile
        self.outputFile = outputFile

        self.parameters = {
            "params": json.dumps(parameters)
        }

    def execute(self, context):
        self.runDate = context['execution_date']
        self.dagName = context['dag'].dag_id
        self.dagfolder = context['dag'].folder

        outputFileName = os.path.join(
            "/home/admin/workflow/output", self.runDate.strftime("%Y-%m-%d_%H_%M"), self.outputFile)
        workingDir = os.path.dirname(outputFileName)

        self.parameters["workflow"] = json.dumps({
            "dagBase": "/home/admin/workflow/dags",
            "dagFolder": self.dagfolder,
            "workingDir": workingDir,
            "fileStore": "/home/admin/workflow/FileStore"
        })

        return_value = self.execute_callable()
        self.log.info("Done. Returned value was: %s", return_value)
        return return_value

    def execute_callable(self):
        outputFileName = os.path.join(
            "/home/admin/workflow/output", self.runDate.strftime("%Y-%m-%d_%H_%M"), self.outputFile)
        workingDir = os.path.dirname(outputFileName)

        res = {}

        if not os.path.isdir(workingDir):
            os.makedirs(workingDir)

        try:
            res = pm.execute_notebook(
                os.path.join(self.dagfolder, self.inputFile),
                os.path.join("/home/admin/workflow/output",
                             self.runDate.strftime("%Y-%m-%d_%H_%M"), self.outputFile),
                cwd=workingDir,
                parameters=self.parameters
            )
        except Exception as ex:
            try:
                print("Render HTML")
                os.system(
                    "jupyter nbconvert --to HTML --no-input {0}".format(outputFileName))
            except:
                print("Render failed")
                pass

            try:
                print("Write Mails")
                # get all mail parameters
                server = smtplib.SMTP(config["Airflow"]["smtp"])
                serverMail = config["Airflow"]["fromMail"]
                toMail = config["Airflow"]["toMail"]
                toMail = [m.replace(" ", "") for m in toMail.split(",")]

                # add special users from aiflow call
                if hasattr(self, 'email') and self.email != None:
                    toMail.extend([m.replace(" ", "")
                                   for m in self.email.split(",")])

                # start to send the mails
                m = toMail[0]

                msg = MIMEMultipart()
                msg['Subject'] = 'Notebook Exec Error'
                msg['From'] = serverMail
                msg['To'] = m
                msg['Cc'] = ", ".join([tm for tm in toMail if tm != m])

                text = "Hi!\nThe PapermillOperator of {} raised an exception".format(
                    self.inputFile)
                part1 = MIMEText(text, 'plain')
                msg.attach(part1)

                try:
                    with open(os.path.splitext(outputFileName)[0]+'.html', 'r') as file:
                        html = file.read()
                    part2 = MIMEText(html, 'html')
                    msg.attach(part2)
                except:
                    pass

                server.sendmail(serverMail, toMail, msg.as_string())
            except:
                print("Error writing mails")

            raise ex

        return res


class LibraryOperator(BaseOperator):
    """
    
    Create libraries for local use and databricks

    Attributes
    ----------
    libFolder : str
        the folder name of the python library
    outputFile : str
        the folder used for the output
    version : str
        version string like 1.0.0
    to_databricks: bool
        copy the library also to databricks
    """
    template_fields = ('templates_dict',)
    template_ext = tuple()
    ui_color = '#f5e569'

    # since we won't mutate the arguments, we should just do the shallow copy
    # there are some cases we can't deepcopy the objects(e.g protobuf).
    shallow_copy_attrs = ('python_callable', 'op_kwargs',)

    @apply_defaults
    def __init__(
            self,
            libFolder,
            outputFolder="",
            version="1.0.0",
            to_databricks=True,
            op_args=None,
            op_kwargs=None,
            templates_dict=None,
            templates_exts=None,
            *args, **kwargs):
        super(LibraryOperator, self).__init__(*args, **kwargs)
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}
        #self.provide_context = provide_context
        self.templates_dict = templates_dict
        if templates_exts:
            self.template_ext = templates_exts

        self.libFolder = libFolder
        self.outputFolder = outputFolder
        self.libName = os.path.basename(self.libFolder)
        self.version = version
        self.to_databricks = to_databricks

        self.whlfile = "{}-{}-py2.py3-none-any.whl".format(
            self.libName, self.version)

    def execute(self, context):
        self.dagfolder = context['dag'].folder
        self.fullLibFolder = os.path.join(self.dagfolder, self.libFolder)

        # create the output of the local library copy
        self.runDate = context['execution_date']
        outputFolder = os.path.join(
            "/home/admin/workflow/output", self.runDate.strftime("%Y-%m-%d_%H_%M"), self.outputFolder, self.libName)

        if not os.path.isdir(outputFolder):
            os.makedirs(outputFolder)

        # copy the library content
        from distutils.dir_util import copy_tree
        copy_tree(self.fullLibFolder, outputFolder)

        # create a temporary directory
        import tempfile
        tempdir = tempfile.TemporaryDirectory()

        # create an basic library in the temp directory
        from pypc.create import Package
        p = Package(self.libName, path=tempdir.name)
        p.new(pkgname=self.libName)

        # copy the library content to the temp folder
        copy_tree(self.fullLibFolder, os.path.join(tempdir.name, self.libName))

        # build the package
        import subprocess
        res = subprocess.call(
            ['python', 'setup.py', 'bdist_wheel'], cwd=tempdir.name)
        if res != 0:
            raise Exception("library build process failed")

        # copy the library package to the local FileStore
        if not os.path.isdir("/home/admin/workflow/FileStore/libs"):
            os.makedirs("/home/admin/workflow/FileStore/libs")
        createdWhlFile = os.listdir(os.path.join(tempdir.name, "dist"))[0]
        from shutil import copyfile
        copyfile(os.path.join(tempdir.name, "dist", createdWhlFile), os.path.join(
            "/home/admin/workflow/FileStore/libs", self.whlfile))

        # sync library file to databricks
        if self.to_databricks:
            dbr = databricks.Databricks()
            dbr.upload_file(os.path.join("libs", self.whlfile))

        # append to libs log
        with open(
                os.path.join(
                    "/home/admin/workflow/output",
                    self.runDate.strftime("%Y-%m-%d_%H_%M"),
                    self.outputFolder,
                    "LibraryOperator"),
                "a") as f:
            f.write("{} => {}".format(self.libName, self.whlfile))

        tempdir.cleanup()

        return True


class DatabricksOperator(BaseOperator):
    """

    Executes a Jupyter Notebook on Databricks


    Attributes
    ----------
    inputFile : str
        the input Jupyter Notebook
    outputFile : str
        the output Jupyter Notebook
    parameters : dict
        additional parameters for the run
    libraries : array
        libraries added to databricks
    new_cluster : dict
        parameters for the cluster to create
    existing_cluster_id : str
        name of an existing cluster
    terminate_cluster : bool
        terminate cluster after finishing the job
    """
    template_fields = ('templates_dict',)
    template_ext = tuple()
    ui_color = '#a9ceff'

    # since we won't mutate the arguments, we should just do the shallow copy
    # there are some cases we can't deepcopy the objects(e.g protobuf).
    shallow_copy_attrs = ('python_callable', 'op_kwargs',)

    @apply_defaults
    def __init__(
            self,
            inputFile,
            outputFile,
            libraries=None,
            parameters=None,
            dry_run=False,
            op_args=None,
            op_kwargs=None,
            new_cluster=None,
            existing_cluster_id=None,
            terminate_cluster=True,
            # provide_context=False,
            templates_dict=None,
            templates_exts=None,
            *args, **kwargs):
        super(DatabricksOperator, self).__init__(*args, **kwargs)
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}
        #self.provide_context = provide_context
        self.templates_dict = templates_dict
        if templates_exts:
            self.template_ext = templates_exts
        self.inputFile = inputFile
        self.outputFile = outputFile
        self.libraries = libraries

        self.parameters = {
            "params": json.dumps(parameters)
        }
        self.new_cluster = new_cluster
        self.existing_cluster_id = existing_cluster_id
        self.terminate_cluster = terminate_cluster if existing_cluster_id else False
        self.dry_run = dry_run

    def add_library(self, lib: LibraryOperator):
        """
        add library to the databricks job
        """
        if not self.libraries:
            self.libraries = []

        user = config["Databricks"]["USER"]

        self.libraries.append(
            {
                "whl":  os.path.join("dbfs:/FileStore/shared_uploads", user, "libs",  lib.whlfile)
            }
        )

        print(self.libraries)

        lib >> self

    def execute(self, context):
        self.runDate = context['execution_date']
        self.dagName = context['dag'].dag_id
        self.dagfolder = context['dag'].folder

        outputFileName = os.path.join(
            "/home/admin/workflow/output", self.runDate.strftime("%Y-%m-%d_%H_%M"), self.outputFile)
        workingDir = os.path.dirname(outputFileName)

        dbr = databricks.Databricks()

        self.parameters["workflow"] = json.dumps({
            "dagBase": dbr._get_fullpath(""),
            "dagFolder": dbr._get_fullpath(os.path.join(self.dagfolder)[26:]),
            "workingDir": workingDir,
            "fileStore": "/dbfs/FileStore/shared_uploads/viktor.krueckl@osram-os.com/"
        })

        return_value = self.execute_callable()
        self.log.info("Done. Returned value was: %s", return_value)
        return return_value

    def execute_callable(self):
        outputFileName = os.path.join(
            "/home/admin/workflow/output", self.runDate.strftime("%Y-%m-%d_%H_%M"), self.outputFile)
        workingDir = os.path.dirname(outputFileName)
        fileName = outputFileName[len(workingDir)+1:]

        res = {}

        if not os.path.isdir(workingDir):
            os.makedirs(workingDir)

        try:

            dbr = databricks.Databricks()

            targetFile = os.path.join(self.dagfolder, self.inputFile)[26:]

            dbr.mkdirs(os.path.dirname(targetFile))

            dbr.import_ipynb(
                os.path.join(self.dagfolder, self.inputFile),
                targetFile)

            job = dbr.assure_job(
                targetFile,
                targetFile,
                self.new_cluster,
                self.existing_cluster_id,
                self.libraries
            )

            if self.dry_run == False:
                print("job_id: {}".format(job["job_id"]))
                run = dbr.run_job(job["job_id"], self.parameters)

                print("run_id: {}".format(run["run_id"]))
                run_res = dbr.await_run(run["run_id"])

                dbr.run_export(run["run_id"], outputFileName)

                if run_res["state"]["result_state"] != "SUCCESS":
                    raise Exception("Databricks run failed")

                if self.terminate_cluster:
                    dbr.terminate_cluster(self.existing_cluster_id)

        except Exception as ex:

            try:
                print("Write Mails")
                # get all mail parameters
                server = smtplib.SMTP(config["Airflow"]["smtp"])
                serverMail = config["Airflow"]["fromMail"]
                toMail = config["Airflow"]["toMail"]
                toMail = [m.replace(" ", "") for m in toMail.split(",")]

                # add special users from aiflow call
                if hasattr(self, 'email') and self.email != None:
                    toMail.extend([m.replace(" ", "")
                                   for m in self.email.split(",")])

                # start to send the mails
                m = toMail[0]

                msg = MIMEMultipart()
                msg['Subject'] = 'Notebook Exec Error'
                msg['From'] = serverMail
                msg['To'] = m
                msg['Cc'] = ", ".join([tm for tm in toMail if tm != m])

                text = "Hi!\nThe DatabricksOperator of {} raised an exception".format(
                    self.inputFile)
                part1 = MIMEText(text, 'plain', 'utf-8')
                msg.attach(part1)

                print(workingDir)
                for fname in [el for el in os.listdir(workingDir) if el.lower().startswith(fileName.lower())]:
                    try:
                        print(fname)
                        print(os.path.join(workingDir, fname))
                        with open(os.path.join(workingDir, fname), 'r') as file:
                            html = file.read().encode('utf-8')
                        part2 = MIMEText(html, 'html', 'utf-8')
                        msg.attach(part2)
                    except:
                        pass

                server.sendmail(serverMail, toMail, msg.as_string())
            except:
                print("Error writing mails")

            raise ex

        return res


class UploadToDatabricks(BaseOperator):
    """

    Copy a file or more from the local FileStore to the Databricks FileStore

    Attributes
    ----------
    inputFile : str, list
        the file to copy to the Databricks FileStore
    """
    template_fields = ('templates_dict',)
    template_ext = tuple()
    ui_color = '#a9ffa9'

    # since we won't mutate the arguments, we should just do the shallow copy
    # there are some cases we can't deepcopy the objects(e.g protobuf).
    shallow_copy_attrs = ('python_callable', 'op_kwargs',)

    @apply_defaults
    def __init__(
            self,
            inputFile,
            op_args=None,
            op_kwargs=None,
            templates_dict=None,
            templates_exts=None,
            *args, **kwargs):
        super(UploadToDatabricks, self).__init__(*args, **kwargs)
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}
        self.templates_dict = templates_dict
        if templates_exts:
            self.template_ext = templates_exts

        self.inputFile = inputFile

    def execute(self, context):
        return_value = self.execute_callable()
        self.log.info("Done. Returned value was: %s", return_value)
        return return_value

    def execute_callable(self):

        dbr = databricks.Databricks()

        if isinstance(self.inputFile, list):
            for el in self.inputFile:
                dbr.upload_file(el)
        else:
            dbr.upload_file(self.inputFile)

        return {}


class DownloadFromDatabricks(BaseOperator):
    """

    Copy a file or more from the Databricks FileStore to the local FileStore

    Attributes
    ----------
    inputFile : str, list
        the file to collect from the Databricks FileStore
    """
    template_fields = ('templates_dict',)
    template_ext = tuple()
    ui_color = '#89cc89'

    # since we won't mutate the arguments, we should just do the shallow copy
    # there are some cases we can't deepcopy the objects(e.g protobuf).
    shallow_copy_attrs = ('python_callable', 'op_kwargs',)

    @apply_defaults
    def __init__(
            self,
            inputFile,
            op_args=None,
            op_kwargs=None,
            templates_dict=None,
            templates_exts=None,
            *args, **kwargs):
        super(DownloadFromDatabricks, self).__init__(*args, **kwargs)
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}
        self.templates_dict = templates_dict
        if templates_exts:
            self.template_ext = templates_exts

        self.inputFile = inputFile

    def execute(self, context):
        return_value = self.execute_callable()
        self.log.info("Done. Returned value was: %s", return_value)
        return return_value

    def execute_callable(self):

        dbr = databricks.Databricks()

        if isinstance(self.inputFile, list):
            for el in self.inputFile:
                dbr.download_file(el)
        else:
            dbr.download_file(self.inputFile)

        return {}
