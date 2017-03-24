FROM centos:6

USER root
RUN yum install -y rpm-build rpmdevtools python-setuptools

RUN mkdir /rpmbuild
VOLUME ["/rpmbuild"]

COPY build.sh /

CMD ["/build.sh"]
