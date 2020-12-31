import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def main():
    # remove pid file if needed
    if os.path.exists("/home/af-hub/airflow/airflow-webserver.pid"):
        os.remove("/home/af-hub/airflow/airflow-webserver.pid")
    
    if "AIRFLOW__CORE__SQL_ALCHEMY_CONN" in os.environ:
        base_uri = os.environ['AIRFLOW__CORE__SQL_ALCHEMY_CONN']

        DATABASE_NAME = base_uri.split("/")[-1]

        #if a special database name is used
        if DATABASE_NAME != "airflow":

            #extract the base connection string
            splits = base_uri.split("/")
            
            admin_database = [s.split("@")[0].split(":")[0] for s in splits if "@" in s and ":" in s][0]
            splits[-1] = admin_database
            DATABASE_URI = "/".join(splits)

            #make the admin connection
            engine = create_engine(DATABASE_URI)

            #create a new database if needed
            session = sessionmaker(bind=engine)()
            session.connection().connection.set_isolation_level(0)
            session.execute("CREATE DATABASE {0}".format(DATABASE_NAME))
            session.connection().connection.set_isolation_level(1)


if __name__ == "__main__":
    main()