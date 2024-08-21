#/bin/bash

# install nodejs
apt-get -y update \
    && apt-get install -y --no-install-recommends apt-utils \
    && curl -sL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs iputils-ping ssh nano sshpass \
    && npm install -g configurable-http-proxy http-proxy \
    && apt install wget


# install updated configurable-http-proxy of jupyterhub
cp /tmp/setup/configproxy.js /usr/lib/node_modules/configurable-http-proxy/lib/configproxy.js    


# install torch
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# install python requirements
pip install Cython && pip install scikit-learn --no-build-isolation
apt-get install -y libxml2-dev libxslt-dev
pip install -r /tmp/setup/requirements.txt

# install jupyter lab extensions
pip install jupyterlab-git==0.42.0
pip install jupyterhub-idle-culler
# && jupyter tensorboard enable
pip install ipympl
# && jupyter labextension install jupyterlab-plotly --no-build \
jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build 
pip install jupyterlab-tabular-data-editor
jupyter labextension install jupyterlab-chart-editor  --no-build 
pip install jupyterlab_proxy_gui 
pip install jupyterlab_latex 
DEBIAN_FRONTEND=noninteractive apt install -yq texlive-xetex texlive-latex-extra fontconfig texlive-lang-german 
# && jupyter labextension install @jupyterlab/latex  --no-build \  #wait for jupyterlab 3.0
pip install jupyter-lsp jedi-language-server
jupyter labextension install @krassowski/jupyterlab-lsp --no-build
#&& pip install jupyter-resource-usage jupyterlab-topbar jupyterlab-system-monitor



# install tensorboard
# pip install git+https://github.com/cliffwoolley/jupyter_tensorboard.git 
# pip install git+https://github.com/chaoleili/jupyterlab_tensorboard.git
pip install jupyterlab-tensorboard-pro~=3.0

# install latex
pip install jupyterlab_latex
apt-get install -y chktex \
    && cd /tmp \
    && wget -q https://github.com/latex-lsp/texlab/releases/download/v4.0.0/texlab-x86_64-linux.tar.gz \
    && tar -xzvf texlab-x86_64-linux.tar.gz \
    && cp ./texlab /usr/bin/ \
    && rm -rf texlab*
# # add markdown jupyter-lsp support
npm install -g unified-language-server


# copy extra fonts
mkdir -p /usr/local/share/fonts
cp /tmp/setup/fonts/* /usr/local/share/fonts

# build jupyter extensions
jupyter lab build --dev-build=False --minimize=True


# create admin user
groupadd admin
useradd -m admin -p admin -s /bin/bash --gid admin
# add docker group and user
groupadd -g 991 docker && usermod -aG docker admin && usermod -aG root admin


# create guest user
useradd -m guest -p guest -s /bin/bash -u 1111 --gid admin


# add acl features
apt-get -y install acl 


# root password
echo 'root:root' | chpasswd


# admin will can the owner of jupyter to install addons as user
chown -R admin:root /usr/local/share/jupyter && chmod -R g+rwX /usr/local/share/jupyter

# copy startup scripts
cp /tmp/setup/run.sh /run.sh
chmod 777 /run.sh


# install extensions
cd /tmp/setup/xtensions/python_af-hub
python setup.py build && pip install .


# copy base workflow to home directory
cp -r /tmp/setup/workflow /home/admin/workflow
chown -R admin:root /home/admin/workflow && chmod -R g+rwX /home/admin/workflow
ln -s /home/admin/workflow /home/guest/


# install supervisord
apt -y install supervisor
cp /tmp/setup/supervisord.conf /etc/supervisor/supervisord.conf


# install airflow
pip install sqlalchemy==1.4.50 apache-airflow==2.8.0 Pydantic==2.5.3 jinja2==3.1.1 flask_bcrypt apache-airflow-providers-cncf-kubernetes pendulum==2.1.2 connexion==2.14.2
mkdir -p /home/admin/airflow/
cp /tmp/setup/airflow.cfg /home/admin/airflow/airflow.cfg
cp /tmp/setup/assure_airflow_db.py /assure_airflow_db.py
cp /tmp/setup/main-jupyterlab-proxy-gui-config.json /home/admin/.jupyterlab-proxy-gui-config.json
cp /tmp/setup/guest-jupyterlab-proxy-gui-config.json /home/guest/.jupyterlab-proxy-gui-config.json

# fix airflow
sed -i "s/if recorded_pid is not None and not same_process and not IS_WINDOWS:/if False:/" /usr/local/lib/python3.11/dist-packages/airflow/jobs/local_task_job_runner.py


# make a run directory
mkdir  /jupyterhub && chown admin:root /jupyterhub && chmod 0700 /jupyterhub && chmod -R g+rwX /jupyterhub
apt install -y libcurl4-openssl-dev libssl-dev && pip install psutil pycurl
pip install pip install PyJWT==2.0.0


# init tensorboard as user
jupyter tensorboard enable --user


# add config for jupyter-resource-usage
mkdir -p /home/admin/.jupyter
cp /tmp/setup/jupyter_notebook_config.py /home/admin/.jupyter/jupyter_notebook_config.py
chown admin:admin -R /home/admin/.jupyter


#create the jupyter-lab config, note ad mapping is used to map ad users to admin
cp /tmp/setup/jupyterhub_config.py /jupyterhub_config.py


#add sudo spawner stuff
apt-get install sudo && pip install sudospawner && cat /tmp/setup/sudoers_addon >> /etc/sudoers && usermod -aG sudo admin
chown admin:root /home/admin && chmod -R g+rwX /home/admin && chmod -R g+rwX /run && chmod -R g+rwX /home

# add kubernetes stuff
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl \
    && wget https://get.helm.sh/helm-v3.8.1-linux-amd64.tar.gz \
    && tar xvf helm-v3.8.1-linux-amd64.tar.gz \
    && install -o root -g root -m 0755 linux-amd64/helm /usr/local/bin/helm \
    && rm -rf linux-amd64


