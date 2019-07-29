apk add clamav

chown clamav:clamav /var/lib/clamav
chmod 755 /var/lib/clamav
ls -la /var/lib

mkdir /var/run/clamav
chown clamav:clamav /var/run/clamav
chmod 755 /var/run/clamav

freshclam -v
