FROM tensorflow/tensorflow:2.5.0rc2-gpu-jupyter


#install nodejs
RUN apt-get -y update \
    && apt-get install -y --no-install-recommends apt-utils \
    && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get install -y nodejs iputils-ping ssh nano

#update pip
#RUN pip install --upgrade pip

#install python requirements
COPY ./core-container/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt


#install jupyterhub
RUN pip install jupyterlab==3.0.14 jupyterhub \
    && npm install -g configurable-http-proxy \
    && pip install oauthenticator PyJWT

#install updated configurable-http-proxy of jupyterhub
#note only one file changed!
COPY ./configurable-http-proxy/lib/configproxy.js \
    /usr/lib/node_modules/configurable-http-proxy/lib/configproxy.js


#install jupyter lab extensions
RUN pip install jupyterlab-git \
    # && pip install --pre jupyter-tensorboard \
    # && jupyter tensorboard enable \
    && pip install ipympl \
    && jupyter labextension install jupyterlab-plotly --no-build \
    && jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build \
    && pip install jupyterlab-spreadsheet-editor jupyterlab-tabular-data-editor\
    && jupyter labextension install jupyterlab-chart-editor  --no-build \
    && pip install jupyterlab_proxy_gui \
    && pip install jupyterlab_latex \
    && DEBIAN_FRONTEND=noninteractive apt install -yq texlive-xetex texlive-latex-extra texlive-generic-extra fontconfig texlive-lang-german \
    # && jupyter labextension install @jupyterlab/latex  --no-build \  #wait for jupyterlab 3.0
    && pip install jupyter-lsp python-language-server[all] \
    && jupyter labextension install @krassowski/jupyterlab-lsp@2.1.4 --no-build \
    && echo "ENDE"


#init tensorboard for users
RUN pip install git+https://github.com/cliffwoolley/jupyter_tensorboard.git \
    && pip install git+https://github.com/chaoleili/jupyterlab_tensorboard.git

# # add latex jupyter-lsp support
RUN apt-get install -y chktex \
    && cd /tmp \
    && wget -q https://github.com/latex-lsp/texlab/releases/download/v2.2.2/texlab-x86_64-linux.tar.gz \
    && tar -xzvf texlab-x86_64-linux.tar.gz \
    && cp ./texlab /usr/bin/ \
    && rm -rf texlab* \
# # add markdown jupyter-lsp support
    && npm install -g unified-language-server

# copy some extra fonts
COPY ./core-container/fonts/* /usr/local/share/fonts/

# build extensions
RUN jupyter lab build --dev-build=False --minimize=False


#create admin user
RUN groupadd admin
RUN useradd -m admin -p admin -s /bin/bash --gid admin
#add docker group and user
RUN groupadd -g 991 docker \
    && usermod -aG docker admin
#create the jupyter-lab config, note ad mapping is used to map ad users to admin
COPY ./core-container/jupyterhub_config.py /jupyterhub_config.py


#create guest user
RUN useradd -m guest -p guest -s /bin/bash -u 1111 --gid admin

#set root password
RUN echo 'root:root' | chpasswd

#admin will can the owner of jupyter to install addons as user
RUN chown -R admin:admin /usr/local/share/jupyter

#create startup scripts
COPY ./core-container/run.sh /run.sh 


#make executable
RUN chmod 777 /run.sh


# install other stuff
COPY ./xtensions /xtensions
RUN chown -R admin:admin /xtensions
WORKDIR /xtensions/python_af-hub
RUN python setup.py build && python setup.py install


# copy base workflow to home directory
COPY ./workflow /home/admin/workflow
RUN chown -R admin:admin /home/admin/workflow
RUN ln -s /home/admin/workflow /home/guest/

#add sudo spawner stuff
COPY ./core-container/sudoers_addon /sudoers_addon
RUN apt-get install sudo && pip install sudospawner && cat /sudoers_addon >> /etc/sudoers

#install supervisord
RUN apt -y install supervisor
COPY ./core-container/supervisord.conf /etc/supervisor/supervisord.conf

#install airflow
RUN pip install apache-airflow==2.0.1 flask_bcrypt dtale SQLAlchemy==1.3.23

#make a run directory
RUN mkdir  /jupyterhub && chown admin:admin /jupyterhub && chmod 0700 /jupyterhub
WORKDIR /jupyterhub
RUN apt install -y libcurl4-openssl-dev libssl-dev && pip install psutil pycurl
RUN pip install pip install PyJWT==2.0.0

#run container as admin
USER admin

#init airflow configuration as user
RUN mkdir -p /home/admin/airflow/
COPY ./core-container/airflow.cfg /home/admin/airflow/airflow.cfg
COPY ./core-container/assure_airflow_db.py /assure_airflow_db.py
COPY ./core-container/main-jupyterlab-proxy-gui-config.json /home/admin/.jupyterlab-proxy-gui-config.json
COPY ./core-container/guest-jupyterlab-proxy-gui-config.json /home/guest/.jupyterlab-proxy-gui-config.json





EXPOSE 5050 5051 4040 4041

ENTRYPOINT ["/run.sh"]
CMD ["start"] # set default arg for entrypoint
