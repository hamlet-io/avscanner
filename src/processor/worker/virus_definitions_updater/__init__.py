import os
import subprocess
from common import loggers


logger = loggers.logging.getLogger('VIRUS_DEFINITIONS_UPDATER')


class VirusDefinitionsUpdater:

    def run(self):
        try:
            VIRUS_DEFINITIONS_DIR = os.environ['VIRUS_DEFINITIONS_DIR']
        except KeyError:
            logger.error('VIRUS_DEFINITIONS_DIR env var is not set!')
            return False
        try:
            VIRUS_DEFINITION_FILES = [
                basepath.strip()
                for basepath in
                os.environ['VIRUS_DEFINITION_FILES'].split(',')
                if basepath
            ]
        except KeyError:
            logger.error('VIRUS_DEFINITION_FILES env var is not set!')
            return False
        logger.info('Starting virus definitions update process')
        # Checking that virus definitions directory exists
        logger.info('Checking definitions files location[%s]...', VIRUS_DEFINITIONS_DIR)
        if os.path.isdir(VIRUS_DEFINITIONS_DIR):
            logger.info('%s exists', VIRUS_DEFINITIONS_DIR)
        else:
            logger.error('%s does not exist!', VIRUS_DEFINITIONS_DIR)
            return False
        # Getting last modification time of the virus definition files
        logger.info('Recording last modification time of %s', VIRUS_DEFINITION_FILES)
        virus_definition_files_mtime = {}
        definition_files = []
        for basepath in VIRUS_DEFINITION_FILES:
            filename = os.path.join(VIRUS_DEFINITIONS_DIR, basepath)
            definition_files.append(filename)
            if os.path.isfile(filename):
                mtime = os.path.getmtime(filename)
                virus_definition_files_mtime[filename] = mtime
                logger.info('%s[%s]', basepath, mtime)
            else:
                logger.info('%s is missing', basepath)

        logger.info('Starting freshclam...')
        try:
            process = subprocess.Popen(
                ['freshclam', f'--datadir={VIRUS_DEFINITIONS_DIR}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                encoding='utf-8'
            )
            process.wait()
            stdout = process.stdout.read()
            stderr = process.stderr.read()
            if stdout:
                logger.info('Updater STDOUT\n%s', stdout)
            if stderr:
                logger.error('Updater STDERR\n%s', stderr)
            # stop if update process failed
            if process.returncode != 0:
                logger.info('Virus definitions update failed!')
                return False
            # Checking that files are updated
            updated_files = []
            for filename, mtime in virus_definition_files_mtime.items():
                if mtime < os.path.getmtime(filename):
                    updated_files.append(filename)
            # creating the lists of missing and not updated files for better logging
            not_updated_files = [
                os.path.relpath(f, VIRUS_DEFINITIONS_DIR)
                for f in virus_definition_files_mtime.keys()
                if f not in updated_files
            ]
            # check that all definition files exist
            missing_definition_files = [
                os.path.relpath(f, VIRUS_DEFINITIONS_DIR)
                for f in definition_files
                if not os.path.isfile(f)
            ]
            # NOTE: changed log type from error to info because during frequent updates
            # it produces a lot of irrelevant log entries.
            if not_updated_files:
                logger.info(
                    'Virus definition update process finished succesfully, '
                    'but files %s are not updated. Probably files are up to date. ',
                    not_updated_files
                )
            # NOTE: missing files are critical because they will not allow clamd to start
            if missing_definition_files:
                logger.error(
                    'Required definition files %s are missing after update. '
                    'This may cause clamd failure. '
                    'Please ispect the problem. '
                    'Details may be found in STDOUT and STDERR logs of freshclam process.',
                    missing_definition_files
                )
            if not missing_definition_files:
                logger.info('Virus definitions updated succesfully!')
                return True
            else:
                return False
        except Exception as e:  # pragma: no cover
            logger.exception(e)
        finally:
            try:
                process.kill()
            except (ProcessLookupError, UnboundLocalError):
                pass


if __name__ == '__main__':
    VirusDefinitionsUpdater().run()
