%{!?python_sitelib: %global python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           mssh-copy-id
Version:        0.0.2
Release:        1%{?dist}
Summary:        Tool to copy SSH keys to multiple servers
License:        MIT
URL:            https://github.com/samuel-phan/mssh-copy-id
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires: python-setuptools
Requires:      python-paramiko >= 1.7
Requires:      python-argparse

%description
mssh-copy-id is a command-line tool to copy SSH keys to multiple servers.

%prep
%setup -n %{name}-%{version}

%build
python setup.py build

%install
python setup.py install --skip-build --root %{buildroot}
mv %{buildroot}%{_bindir}/mssh-copy-id.py %{buildroot}%{_bindir}/mssh-copy-id

%check

%files
%doc LICENSE.txt PKG-INFO README.md
%{_bindir}/*
%{python_sitelib}/*

%changelog
* Thu Jun 15 2016 Samuel Phan <samuel@quoonel.com> 0.0.1
- Initial package
