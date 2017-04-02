FROM ubuntu:14.04

USER root
RUN sudo apt-get update
RUN sudo apt-get install -y build-essential debhelper dh-make python-all python-setuptools

RUN mkdir /deb
VOLUME ["/deb"]

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY build.sh /

RUN sudo apt-get clean

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/build.sh"]
