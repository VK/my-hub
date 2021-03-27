#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A small MLflow FastAPI server for pyfunc models"""

from mlflow.tracking import MlflowClient
import mlflow.pyfunc
import mlflow
from fastapi import FastAPI, Request, HTTPException, Depends
import fastapi
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import List
from fastapi.logger import logger
import logging

from starlette.routing import RedirectResponse
from starlette.routing import Route as starlette_Route

import re
import urllib
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
import datetime


# register route
import requests
import os
import json
import configparser
config = configparser.ConfigParser()
config.read('/defaults.cfg')
headers = {'Authorization': "access_token {}".format(
    config["ConfigurableHTTPProxy"]["auth_token"])}
baseurl = "http://127.0.0.1:8001"
requests.post("{}/api/routes/user/admin/models/".format(baseurl), headers=headers,
              data=json.dumps({'target': 'http://localhost:4041', 'cookiecheck': False}))

# connect to mlflow
mlflow.set_tracking_uri("http://localhost:4040")
client = MlflowClient()


def load_artifact(run_id, artifact_path):
    params = {"path": artifact_path,
              "run_uuid": run_id}
    res = requests.get(
        "http://localhost:4040/user/admin/mlflow/get-artifact", params=params)
    return res


basepath = "/user/admin/models"
staging = False
basepath_re = "^" + basepath.replace("/", "\\/")+"\\/"

tags_metadata = [
    {
        "name": "Metadata",
        "description": "Get meta information of the models.",
    },
    {
        "name": "Models",
        "description": "Predict with the models.",
    }
]

app = FastAPI(root_path=basepath, redoc_url=None, tags_metadata=tags_metadata)
security = HTTPBearer()
valid_tokens = [val for kev, val in config["MLflowModelServerTokens"].items()]


def check_token(token):
    if token.credentials in valid_tokens:
        return True
    raise HTTPException(
        status_code=401,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
logger.setLevel(gunicorn_logger.level)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="MLflow Models",
        version="1.0.0",
        description="All local MLflow models",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

for r in app.routes:
    if not isinstance(r, fastapi.routing.APIRoute):
        r.path_regex = re.compile(r.path_regex.pattern.replace(
            '^\\/', basepath_re), re.UNICODE)


async def redirect_to_docs(data):
    response = RedirectResponse(url=basepath+'/docs')
    return response
app.routes.append(starlette_Route(basepath, redirect_to_docs))
app.routes.append(starlette_Route(basepath+"/", redirect_to_docs))


model_dict = {}


def get_version(m):
    prod_models = [
        mm for mm in m.latest_versions if mm.current_stage == "Production"]
    stage_models = [
        mm for mm in m.latest_versions if mm.current_stage == "Staging"]

    if staging and len(stage_models) > 0:
        return stage_models[0]
    if len(prod_models) > 0:
        return prod_models[0]
    return m.latest_versions[0]


class PyFuncHandler:

    dtype_sample = {
        "float64": 1.234,
        "float32": 1.234,
        "int": 1,
        "int64": 1,
        "int32": 1,
        "str": "A",
    }

    def __init__(self, name, model_version, description):
        try:
            model = mlflow.pyfunc.load_model(model_version.source)
            input_schema = model.metadata.get_input_schema()
            output_schema = model.metadata.get_output_schema()
        except:
            model = None
            input_schema = None
            output_schema = None

        try:
            res = load_artifact(model_version.run_id, os.path.join(model.metadata.artifact_path,
                                model.metadata.saved_input_example_info['artifact_path']
                                                                   ))
            input_example_data = res.json()['inputs']
        except:
            input_example_data = {}

        input_schema_class = type(name+"-input",
                                  (BaseModel, ),
                                  {el["name"]:
                                   input_example_data[el["name"]]
                                   if el["name"] in input_example_data else
                                   self.get_example_el(el) for el in input_schema.to_dict()})

        try:
            np_input = self.numpy_input(input_example_data, input_schema)
            output_example_data = model.predict(np_input)
            output_example_data = {k:v.tolist() for k,v in output_example_data.items()}
        except:
            output_example_data = {}

        output_schema_class = type(name+"-output",
                                   (BaseModel, ),
                                   {el["name"]:
                                    output_example_data[el["name"]]
                                    if el["name"] in output_example_data else
                                    self.get_example_el(el) for el in output_schema.to_dict()})

        self.version = model_version.version
        self.source = model_version.source
        self.run_id = model_version.run_id
        self.model = model
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.input_schema_class = input_schema_class()
        self.output_schema_class = output_schema_class()

        long_description = f"""{description}

<b>Input Schema:</b> {self.get_schema_string(input_schema)} <br/>
<b>Output Schema:</b> {self.get_schema_string(output_schema)}<br/>
<b>Version: </b> {self.get_version_link(name, model_version)}<br/>
<b>Run: </b> {self.get_experiment_link(model_version)}
        """

        @app.post(basepath+'/'+name, description=long_description, name=name, tags=["Models"], response_model=output_schema_class)
        async def func(data: input_schema_class, token: str = Depends(security)):
            check_token(token)

            try:
                np_input = self.numpy_input(data.__dict__, input_schema)
            except Exception as ex:
                raise self.get_error_message("Parse input error", ex)

            try:
                output = model.predict(np_input)
            except Exception as ex:
                raise self.get_error_message("Model prediction error", ex)

            try:
                output = self.parse_output(output)
            except Exception as ex:
                raise self.get_error_message("Parse output error", ex)

            return output

    def get_version_link(self, name, model_version):
        url = f"/user/admin/mlflow/#/models/{name}/versions/{model_version.version}"
        return f"<a href=\"{url}\">{model_version.version}</a>"

    def get_experiment_link(self, model_version):
        source = model_version.source
        url = source.replace("/home/admin/mlflow",
                             "/user/admin/mlflow/#/experiments")
        url = re.sub(r'/artifacts.*', '', url)
        parts = url.split("/")
        parts.insert(7, "runs")
        url = "/".join(parts)
        return f"<a href=\"{url}\">{model_version.run_id}</a>"

    def get_nested(self, dtype, shape):
        if len(shape) == 1:
            return [self.dtype_sample[dtype]]*shape[0]
        else:
            return [self.get_nested(dtype, shape[1:])]*max(1, shape[0])

    def get_example_el(self, el):
        if el["type"] == 'tensor':
            return self.get_nested(**el["tensor-spec"])
        return None

    def numpy_input(self, data, input_cfg):
        types = {el["name"]: el["tensor-spec"]["dtype"]
                 for el in input_cfg.to_dict()}
        return {
            key: np.array(val).astype(types[key])
            for key, val in data.items()
        }

    def get_error_message(self, loc, ex):
        return HTTPException(status_code=442, detail=[
            {
                "loc": [loc],
                "msg": str(ex),
                "type": str(type(ex))
            }
        ])

    def parse_output(self, data):
        return {
            key: val.tolist() if isinstance(val, (np.ndarray, np.generic)) else val
            for key, val in data.items()
        }

    def get_schema_string(self, schema):
        return "<ul><li>" + \
            '</li><li>'.join([
                '<b>'+s.name+'</b>: ' +
                str(s).replace('\''+s.name+'\':', '')
                for s in schema.inputs]) + \
            '</li></ul>'


def update_models():
    global model_dict

    for m in client.list_registered_models():

        # get model information
        name = urllib.parse.quote_plus(m.name)
        description = m.description

        # get the best version
        model_version = get_version(m)

        # if the currently loaded model is already ok
        if name in model_dict and model_version.run_id == model_dict[name].run_id:
            continue

        logger.info(f"Update model {name}")

        # delete old route
        for idx2 in [idx for idx, r in enumerate(app.routes) if r.path == basepath+"/"+name]:
            del app.routes[idx2]

        # create new handler
        model_dict[name] = PyFuncHandler(name, model_version, description)

    app.openapi_schema = None


scheduler = BackgroundScheduler()
scheduler.add_job(func=update_models, trigger="interval", seconds=300)
scheduler.add_job(func=update_models,
                  trigger="date",
                  run_date=datetime.datetime.now()
                  + datetime.timedelta(seconds=10))
scheduler.start()

if __name__ == "__main__":
    import uvicorn
    logger.setLevel(logging.DEBUG)
    update_models()
    uvicorn.run(app, port=4041)

