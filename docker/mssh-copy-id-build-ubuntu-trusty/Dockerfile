FROM ubuntu:trusty

USER root
RUN sudo apt-get update
RUN sudo apt-get install -y build-essential debhelper dh-make python-all python-setuptools

RUN mkdir /deb
VOLUME ["/deb"]

COPY _work/sudo-as-user.sh /usr/local/bin/sudo-as-user.sh
COPY build.sh /

RUN sudo apt-get clean

ENTRYPOINT ["/usr/local/bin/sudo-as-user.sh"]
CMD ["/build.sh"]
