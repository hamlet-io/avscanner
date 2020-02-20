#!/usr/bin/env bash

function main() {

  # Select way we want to run the app - default is "AVSCANNER"
    APP_RUN_MODE="${APP_RUN_MODE:-AVSCANNER}"
    echo "Starting in ${APP_RUN_MODE} mode"
    case "${APP_RUN_MODE}" in
        TASK)
            # Run one off tasks, each separated by ";"
            if [[ -n "${APP_TASK_LIST}" ]]; then
                IFS=';' read -ra CMDS <<< "${APP_TASK_LIST}"
                for CMD in "${CMDS[@]}"; do
                    echo "Starting task \"python manage.py ${CMD}\""
                    python manage.py ${CMD}
                    RESULT=$? && [[ "${RESULT}" -ne 0 ]] && exit
                done
            fi
            echo  "Tasks completed"
            exit
        ;;
        *)
            ENTRYPOINT_SCRIPT="./docker/scripts/entrypoint-${APP_RUN_MODE,,}.sh"
            if [[ -f "${ENTRYPOINT_SCRIPT}" ]]; then
                ${ENTRYPOINT_SCRIPT} "$@"
                KILL_LIST+=($!)
		        echo "DEBUG: my KILL_LIST is '$KILL_LIST'"
            else
                echo "ERROR: entrypoint script missing for ${APP_RUN_MODE} mode"
                RESULT=2 && exit
            fi
        ;;
    esac

}
# echo "Sleeping to prevent exit..."
# while true; do sleep 10s; done
# recording start timestamp to use it in the worker's logs
export START_TIMESTAMP="$(date +%s)"
echo "START TIMESTAMP=$START_TIMESTAMP"
main "$@"
