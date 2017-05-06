FROM centos:latest

USER root

RUN echo 'root:root_password' | chpasswd
RUN yum install -y openssh-server iproute
RUN ssh-keygen -A
RUN mkdir -m 700 /root/.ssh

RUN yum clean all

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
