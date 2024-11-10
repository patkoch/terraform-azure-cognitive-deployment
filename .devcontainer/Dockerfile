FROM ubuntu:22.04

# update and install sudo
RUN apt-get update && \
    apt-get -y install sudo
# install curl
RUN sudo apt-get install curl -y
# install azure cli
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
# install terraform
RUN apt-get update && apt-get install -y gnupg software-properties-common curl wget git && \
    curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add - && \
    apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main" && \
    apt-get update && apt-get install terraform -y
# update and install wget and git
RUN apt-get update && apt-get install -y \
    wget \
    git