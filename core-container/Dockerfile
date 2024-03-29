#FROM tensorflow/tensorflow:2.8.0-jupyter
FROM tensorflow/tensorflow:2.15.0-gpu-jupyter


#install nodejs
RUN apt-get -y update \
    && apt-get install -y --no-install-recommends apt-utils \
    && curl -sL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs iputils-ping ssh nano sshpass \
    && npm install -g configurable-http-proxy

#install updated configurable-http-proxy of jupyterhub
#note only one file changed!
COPY ./configurable-http-proxy/lib/configproxy.js \
    /usr/lib/node_modules/configurable-http-proxy/lib/configproxy.js

#install python requirements
COPY ./core-container/requirements.txt /requirements.txt
RUN pip install Cython && pip install scikit-learn --no-build-isolation 
RUN apt-get install -y libxml2-dev libxslt-dev
RUN pip install -r /requirements.txt

#install jupyter lab extensions
RUN pip install jupyterlab-git==0.42.0 \
    && pip install jupyterhub-idle-culler \
    # && jupyter tensorboard enable \
    && pip install ipympl \
    # && jupyter labextension install jupyterlab-plotly --no-build \ 
    && jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build \
    && pip install jupyterlab-tabular-data-editor\
    && jupyter labextension install jupyterlab-chart-editor  --no-build \
    && pip install jupyterlab_proxy_gui \
    #&& pip install jupyterlab_latex \
    && DEBIAN_FRONTEND=noninteractive apt install -yq texlive-xetex texlive-latex-extra fontconfig texlive-lang-german \
    # && jupyter labextension install @jupyterlab/latex  --no-build \  #wait for jupyterlab 3.0
    && pip install jupyter-lsp jedi-language-server \
    && jupyter labextension install @krassowski/jupyterlab-lsp --no-build \
    #&& pip install jupyter-resource-usage jupyterlab-topbar jupyterlab-system-monitor \
    && echo "ENDE"


# install git tensorbord 
RUN pip install git+https://github.com/cliffwoolley/jupyter_tensorboard.git \
    && pip install git+https://github.com/chaoleili/jupyterlab_tensorboard.git

# install git jupyterlab-latex
RUN pip install jupyterlab_latex
# RUN cd / \
#     && git clone https://github.com/joequant/jupyterlab-latex.git \
#     && cd jupyterlab-latex \
#     && jlpm install \
#     && jlpm run build \
#     && jupyter labextension install . --no-build \
#     && python setup.py build \
#     && pip install . \
#     && cd / \
#     && rm -rf jupyterlab-latex

# add latex jupyter-lsp support
RUN apt-get install -y chktex \
    && cd /tmp \
    #&& wget -q https://github.com/latex-lsp/texlab/releases/download/v2.2.2/texlab-x86_64-linux.tar.gz \
    && wget -q https://github.com/latex-lsp/texlab/releases/download/v4.0.0/texlab-x86_64-linux.tar.gz \
    && tar -xzvf texlab-x86_64-linux.tar.gz \
    && cp ./texlab /usr/bin/ \
    && rm -rf texlab* \
# # add markdown jupyter-lsp support
    && npm install -g unified-language-server

# copy some extra fonts
COPY ./core-container/fonts/* /usr/local/share/fonts/

# build extensions
# RUN jupyter lab build --dev-build=False --minimize=False
RUN jupyter lab build --dev-build=False --minimize=True


#create admin user
RUN groupadd admin
RUN useradd -m admin -p admin -s /bin/bash --gid admin
#add docker group and user
RUN groupadd -g 991 docker \
    && usermod -aG docker admin && usermod -aG root admin

#create guest user
RUN useradd -m guest -p guest -s /bin/bash -u 1111 --gid admin

#set root password
RUN echo 'root:root' | chpasswd

#admin will can the owner of jupyter to install addons as user
RUN chown -R admin:root /usr/local/share/jupyter && chmod -R g+rwX /usr/local/share/jupyter

#create startup scripts
COPY ./core-container/run.sh /run.sh 


#make executable
RUN chmod 777 /run.sh


# install other stuff
COPY ./xtensions /xtensions
RUN chown -R admin:root /xtensions && chmod -R g+rwX /xtensions
WORKDIR /xtensions/python_af-hub
RUN python setup.py build && pip install .


# copy base workflow to home directory
COPY ./workflow /home/admin/workflow
RUN chown -R admin:root /home/admin/workflow && chmod -R g+rwX /home/admin/workflow
RUN ln -s /home/admin/workflow /home/guest/

#install supervisord
RUN apt -y install supervisor
COPY ./core-container/supervisord.conf /etc/supervisor/supervisord.conf

#install airflow
# RUN pip install apache-airflow==2.2.4 flask_bcrypt dtale SQLAlchemy==1.4.32
RUN pip install sqlalchemy==1.4.50 apache-airflow==2.8.0 Pydantic==2.5.3 jinja2==3.1.1 flask_bcrypt apache-airflow-providers-cncf-kubernetes pendulum==2.1.2 connexion==2.14.2
# crude fix local_task nested pidsls
# RUN sed -i 's/same_process = recorded_pid == current_pid/same_process = True/g' /usr/local/lib/python3.8/dist-packages/airflow/jobs/local_task_job.py


#make a run directory
RUN mkdir  /jupyterhub && chown admin:root /jupyterhub && chmod 0700 /jupyterhub && chmod -R g+rwX /jupyterhub
WORKDIR /jupyterhub
RUN apt install -y libcurl4-openssl-dev libssl-dev && pip install psutil pycurl
RUN pip install pip install PyJWT==2.0.0

# add acl
RUN apt-get -y install acl 



#init airflow configuration as user
RUN mkdir -p /home/admin/airflow/
COPY ./core-container/airflow.cfg /home/admin/airflow/airflow.cfg
COPY ./core-container/assure_airflow_db.py /assure_airflow_db.py
COPY ./core-container/main-jupyterlab-proxy-gui-config.json /home/admin/.jupyterlab-proxy-gui-config.json
COPY ./core-container/guest-jupyterlab-proxy-gui-config.json /home/guest/.jupyterlab-proxy-gui-config.json

# init tensorboard as user
RUN jupyter tensorboard enable --user

# add config for jupyter-resource-usage
COPY ./core-container/jupyter_notebook_config.py /home/admin/.jupyter/jupyter_notebook_config.py

#create the jupyter-lab config, note ad mapping is used to map ad users to admin
COPY ./core-container/jupyterhub_config.py /jupyterhub_config.py

#add sudo spawner stuff
COPY ./core-container/sudoers_addon /sudoers_addon
RUN apt-get install sudo && pip install sudospawner && cat /sudoers_addon >> /etc/sudoers && usermod -aG sudo admin
RUN chown admin:root /home/admin && chmod -R g+rwX /home/admin && chmod -R g+rwX /run && chmod -R g+rwX /home


# add kubernetes stuff
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl \
    && wget https://get.helm.sh/helm-v3.8.1-linux-amd64.tar.gz \
    && tar xvf helm-v3.8.1-linux-amd64.tar.gz \
    && install -o root -g root -m 0755 linux-amd64/helm /usr/local/bin/helm \
    && rm -rf linux-amd64

# add mongodump
RUN cd /tmp && wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian10-x86_64-100.5.2.deb \
    && dpkg -i mongodb-database-tools-debian10-x86_64-100.5.2.deb \ 
    && rm -f mongodb-database-tools-debian10-x86_64-100.5.2.deb


# fix airflow
RUN sed -i "s/if recorded_pid is not None and not same_process and not IS_WINDOWS:/if False:/" /usr/local/lib/python3.11/dist-packages/airflow/jobs/local_task_job_runner.py

# fix hyperopt mongo  replace "j=" with "journal=" 
RUN sed -i 's/j=/journal=/g' /usr/local/lib/python3.11/dist-packages/hyperopt/mongoexp.py
RUN sed -i 's/rval = self.handle.jobs.find(query).count()/rval = len(list(self.handle.jobs.find(query)))/g' /usr/local/lib/python3.11/dist-packages/hyperopt/mongoexp.py
# pip install pymongo==3.13.0?

#run container as admin
USER admin

EXPOSE 5050 5051 4040 4041

ENTRYPOINT ["/run.sh"]
CMD ["start"] # set default arg for entrypoint
