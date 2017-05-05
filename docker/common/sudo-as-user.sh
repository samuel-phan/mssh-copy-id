#!/bin/bash

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback

USER_ID=${LOCAL_USER_ID:-9001}

echo "Starting with UID : $USER_ID"
if [ "$USER_ID" -ne "0" ]; then
    useradd --shell /bin/bash -u $USER_ID -o user
    echo "user        ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers
    sudo -u user "$@"
else
    sudo -u root "$@"
fi
