apk update && apk add make
pip install --upgrade pip
pip install -r /processor/requirements.txt
apk add clamav
freshclam

mkdir /var/run/clamav
chown clamav:clamav /var/run/clamav
chmod 750 /var/run/clamav
