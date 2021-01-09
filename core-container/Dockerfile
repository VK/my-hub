FROM tensorflow/tensorflow:2.2.1-gpu-jupyter

#install nodejs
RUN apt-get install -y --no-install-recommends apt-utils \
    && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && apt-get install -y nodejs iputils-ping ssh nano

#update pip
#RUN pip install --upgrade pip

#install python requirements
COPY ./core-container/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt


#install jupyterhub
RUN pip install jupyterlab==2.2.9 jupyterhub \
    && npm install -g configurable-http-proxy \
    && pip install oauthenticator PyJWT

#install updated configurable-http-proxy of jupyterhub
#note only one file changed!
COPY ./configurable-http-proxy/lib/configproxy.js \
    /usr/lib/node_modules/configurable-http-proxy/lib/configproxy.js


#install jupyter lab extensions
RUN pip install --upgrade jupyterlab-git \
    && pip install --pre jupyter-tensorboard \
    && jupyter tensorboard enable \
    && jupyter labextension install jupyterlab_tensorboard --no-build \
    && pip install ipympl \
    && jupyter labextension install jupyterlab-plotly --no-build \
    && jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build \
    && jupyter labextension install jupyterlab-spreadsheet --no-build \
    && jupyter labextension install jupyterlab-chart-editor  --no-build \
    && pip install jupyterlab_proxy_gui \
    && pip install jupyterlab_latex \
    && DEBIAN_FRONTEND=noninteractive apt install -yq texlive-xetex texlive-latex-extra texlive-generic-extra fontconfig \
    && jupyter labextension install @jupyterlab/latex  --no-build \
    && jupyter labextension install @jupyterlab/toc --no-build \
    && pip install jupyter-lsp python-language-server[all] \
    && jupyter labextension install @krassowski/jupyterlab-lsp --no-build

# copy some extra fonts
COPY ./core-container/fonts/* /usr/local/share/fonts/

# update and build extensions
RUN jupyter labextension update --all --no-build \
    && jupyter lab build --dev-build=False --minimize=False


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
RUN pip install apache-airflow flask_bcrypt dtale

#run container as admin
USER admin

#init airflow configuration as user
RUN mkdir -p /home/admin/airflow/
COPY ./core-container/airflow.cfg /home/admin/airflow/airflow.cfg
COPY ./core-container/assure_airflow_db.py /assure_airflow_db.py
COPY ./core-container/main-jupyterlab-proxy-gui-config.json /home/admin/.jupyterlab-proxy-gui-config.json
COPY ./core-container/guest-jupyterlab-proxy-gui-config.json /home/guest/.jupyterlab-proxy-gui-config.json


#init tensorboard for users
RUN jupyter tensorboard enable --user \
    && pip install tensorboard==2.2.0




ENTRYPOINT ["/run.sh"]
CMD ["start"] # set default arg for entrypoint
