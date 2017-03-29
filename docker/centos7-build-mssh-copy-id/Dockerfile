FROM centos:7

USER root
RUN yum install -y rpm-build rpmdevtools python-setuptools sudo

RUN mkdir /rpmbuild
VOLUME ["/rpmbuild"]

COPY entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["rpmbuild", "--define", "_topdir /rpmbuild", "-ba", "/rpmbuild/SPECS/mssh-copy-id.spec"]
