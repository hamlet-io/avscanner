# simple test just to check that worker runs
import os
import time
from unittest import mock
import tempfile
from processor.worker.virus_definitions_updater import VirusDefinitionsUpdater


def test():
    VirusDefinitionsUpdater().run()


@mock.patch('processor.worker.virus_definitions_updater.subprocess.Popen')
def test_mocked(Popen):

    VIRUS_DEFINITIONS_DIR = tempfile.mkdtemp()
    VIRUS_DEFINITION_FILES = 'definitions-monthly,definitions-daily'

    with mock.patch.dict(
        'os.environ',
        {
            'VIRUS_DEFINITIONS_DIR': VIRUS_DEFINITIONS_DIR,
            'VIRUS_DEFINITION_FILES': VIRUS_DEFINITION_FILES
        }
    ):
        process_mock = mock.MagicMock()

        process_mock.stderr.read.return_value = 'Error text'
        process_mock.stdout.read.return_value = 'Info text'
        process_mock.kill.side_effect = ProcessLookupError()

        def create_update_files(*args, **kwargs):
            time.sleep(1)
            for basename in VIRUS_DEFINITION_FILES.split(','):
                with open(os.path.join(VIRUS_DEFINITIONS_DIR, basename), 'at+') as f:
                    f.write('line')
            return process_mock

        # testing error updater failed
        process_mock.returncode = 1
        Popen.return_value = process_mock
        assert not VirusDefinitionsUpdater().run()
        Popen.reset_mock()
        # testing error files still missing
        process_mock.returncode = 0
        Popen.return_value = process_mock
        assert not VirusDefinitionsUpdater().run()
        Popen.assert_called_once()
        Popen.reset_mock()

        Popen.side_effect = create_update_files
        # testing success files missing
        process_mock.returncode = 0
        assert VirusDefinitionsUpdater().run()
        Popen.assert_called_once()
        Popen.reset_mock()
        # testing success files updated
        process_mock.returncode = 0
        Popen.side_effect = create_update_files
        assert VirusDefinitionsUpdater().run()
        Popen.assert_called_once()
        Popen.reset_mock()
        # testing no updater error, but files not updated
        Popen.side_effect = None
        assert not VirusDefinitionsUpdater().run()
        Popen.assert_called_once()
        Popen.reset_mock()
        # testing missing env var VIRUS_DEFINITIONS_DIR
        with mock.patch.dict('os.environ'):
            del os.environ['VIRUS_DEFINITIONS_DIR']
            assert not VirusDefinitionsUpdater().run()
            Popen.assert_not_called()
            Popen.reset_mock()
        # testing missing env var VIRUS_DEFINITION_FILES
        with mock.patch.dict('os.environ'):
            del os.environ['VIRUS_DEFINITION_FILES']
            assert not VirusDefinitionsUpdater().run()
            Popen.assert_not_called()
            Popen.reset_mock()
        # testing VIRUS_DEFINITIONS_DIR does not exist
        with mock.patch.dict('os.environ'):
            temp_dir = tempfile.mkdtemp()
            os.environ['VIRUS_DEFINITIONS_DIR'] = temp_dir
            os.rmdir(temp_dir)
            assert not VirusDefinitionsUpdater().run()
            Popen.assert_not_called()
            Popen.reset_mock()
