FROM centos:6

USER root

RUN mkdir -m 700 /root/.ssh

COPY _work/mssh-copy-id-*.rpm /
RUN yum install -y /mssh-copy-id*.rpm openssh-clients iproute
RUN yum clean all

VOLUME ["/root/.ssh"]

ENTRYPOINT ["/usr/bin/mssh-copy-id"]
