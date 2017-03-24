FROM centos:latest

USER root

RUN echo 'root:root' | chpasswd
RUN yum install -y openssh-server
RUN ssh-keygen -A
RUN mkdir -m 700 /root/.ssh

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
