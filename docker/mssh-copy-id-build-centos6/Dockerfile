FROM centos:6

USER root
RUN yum install -y rpm-build rpmdevtools python-setuptools sudo

RUN mkdir /rpmbuild
VOLUME ["/rpmbuild"]

COPY _work/sudo-as-user.sh /usr/local/bin/sudo-as-user.sh

RUN yum clean all

ENTRYPOINT ["/usr/local/bin/sudo-as-user.sh"]
CMD ["rpmbuild", "--define", "_topdir /rpmbuild", "-ba", "/rpmbuild/SPECS/mssh-copy-id.spec"]
