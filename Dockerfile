# Base Image
FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# Enable Networking on port 8001 (apache)
EXPOSE 8001

# Install dependencies
RUN apt-get update && apt-get install -y \
    locales \
    git \
    wget curl gnupg \
    python3-pip virtualenv libsm6 libxrender1 libfontconfig1 \
    apache2 libapache2-mod-wsgi-py3 \
    && rm -rf /var/lib/apt/lists/*

# WHen git pull is added to run_deploy.py, --remote-submodules is no longer needed
## Install recent version of git that supports --remote-submodules
#RUN apt-get update && apt-get install -y software-properties-common
#RUN apt-add-repository -y ppa:git-core/ppa
#RUN apt-get install -y git

# install latest node
RUN curl -sL https://deb.nodesource.com/setup_16.x  | bash - && apt-get -y install nodejs

# setup locale
RUN locale-gen en_US.UTF-8

# setup basic npm packages
RUN npm install npm@latest -g && npm install -g @angular/cli

# basic dirs
RUN mkdir -p /opt

# Disable cache for git clone
RUN echo "busting cache again 5"
# clone code and all its dependencies. Trying without --remote-submodules.
RUN git clone --recursive http://github.com/hajicj/ommr4all-deploy

# setup apache
RUN cp ommr4all-deploy/ommr4all-deploy/deploy/apache2.conf /etc/apache2/sites-available/ommr4all.conf && a2ensite ommr4all.conf && apachectl configtest

# run deploy script steps
RUN cd ommr4all-deploy && python3 ommr4all-deploy/deploy.py --client --submodules_bleedingedge --dbdir /opt/ommr4all/storage
RUN cd ommr4all-deploy && python3 ommr4all-deploy/deploy.py --venv --dbdir /opt/ommr4all/storage
RUN cd ommr4all-deploy && python3 ommr4all-deploy/deploy.py --server --submodules_bleedingedge --dbdir /opt/ommr4all/storage
RUN cd ommr4all-deploy && python3 ommr4all-deploy/deploy.py --submodules --submodules_bleedingedge --dbdir /opt/ommr4all/storage
RUN cd ommr4all-deploy && python3 ommr4all-deploy/deploy.py --calamari --dbdir /opt/ommr4all/storage
RUN cd ommr4all-deploy && python3 ommr4all-deploy/deploy.py --serversettings --dbdir /opt/ommr4all/storage
RUN cd ommr4all-deploy && python3 ommr4all-deploy/deploy.py --staticfiles --dbdir /opt/ommr4all/storage
RUN cd ommr4all-deploy && python3 ommr4all-deploy/deploy.py --migrations --dbdir /opt/ommr4all/storage

# launch apache
CMD apachectl -D FOREGROUND
