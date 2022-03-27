import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def main():

    db_created = False

    # remove pid file if needed
    if os.path.exists("/home/admin/airflow/airflow-webserver.pid"):
        os.remove("/home/admin/airflow/airflow-webserver.pid")

    if "AIRFLOW__CORE__SQL_ALCHEMY_CONN" in os.environ:

        try:
            base_uri = os.environ['AIRFLOW__CORE__SQL_ALCHEMY_CONN']

            DATABASE_NAME = base_uri.split("/")[-1]

            # extract the base connection string and replace the schema name with the username
            splits = base_uri.split("/")
            admin_database = [s.split("@")[0].split(":")[0]
                              for s in splits if "@" in s and ":" in s][0]
            splits[-1] = admin_database
            DATABASE_URI = "/".join(splits)

            # make the admin connection
            engine = create_engine(DATABASE_URI)

            # create a new database if needed
            session = sessionmaker(bind=engine)()
            session.connection().connection.set_isolation_level(0)
            session.execute("CREATE DATABASE {0}".format(DATABASE_NAME))
            session.connection().connection.set_isolation_level(1)

            db_created = True
        except:
            print("Did not create a new airflow db")

        if db_created:
            # call airflow to init database
            try:
                os.system("airflow db init")
            except:
                print("Error in airflow db init")

            # create dummy admin airflow user
            try:
                os.system(
                    "airflow users create -u admin -p admin -e admin@admin.de -f admin -l admin -r Admin")
            except:
                print("Error in airflow users create")


if __name__ == "__main__":
    main()
