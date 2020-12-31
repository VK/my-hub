def get_client():
    """
    Initialize a remote mlflow connection and return the client
    """
    import mlflow
    from mlflow.tracking.client import MlflowClient
    import configparser
    import os

    config = configparser.ConfigParser()
    config.read('/defaults.cfg')

    os.environ["MLFLOW_TRACKING_TOKEN"] = config["Databricks"]["TOKEN"]

    mlflow.set_tracking_uri(config["Databricks"]["REGISTRY"])
    mlflow.set_registry_uri(config["Databricks"]["REGISTRY"])

    return MlflowClient()