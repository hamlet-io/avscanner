#!/usr/bin/env bash

cd ..

. "${AUTOMATION_BASE_DIR}/common.sh"
dockerstagedir="$(getTempDir "cota_docker_XXXXXX" "${DOCKER_STAGE_DIR}")"
chmod a+rwx "${dockerstagedir}"
cp -r ./src/ ${dockerstagedir}/
mkdir --parents ${dockerstagedir}/minio/data/archive
mkdir --parents ${dockerstagedir}/minio/data/quarantine
mkdir --parents ${dockerstagedir}/minio/data/unprocessed

ls -la ${dockerstagedir}
dockerstagedir=${dockerstagedir} make ci

cp ${dockerstagedir}/src/test-report.xml ${AUTOMATION_BUILD_SRC_DIR}/test-report.xml


exit $?