import os
import shutil

import pytest

from .core import PythonScriptsCronManager


def test_core():
    with open(f'{os.path.abspath("./python_scs")}/test_cronfile', 'w+') as cron_file:
        pass

    manager = PythonScriptsCronManager(
        app_path=os.path.abspath('./python_scs'),
        crontab_tabfile='/test_cronfile'
    )

    manager.clear_jobs()
    assert manager.get_jobs() == []

    manager.upload_script('script_test', b'print("foo")')
    assert manager.get_scripts() == ['script_test.py']

    script_job = manager.set_script_job('script_test.py', ['*', '*', '*', '*', '*'], comment='foo')
    assert script_job in manager.get_jobs()

    assert manager.get_job(script_name='script_test.py')
    assert manager.get_job(comment='foo')

    assert not manager.get_job(script_name='unexistent')
    assert not manager.get_job(comment='unexistent')
    assert not manager.get_job(command='unexistent')
    assert not manager.get_job(marker='unexistent')

    custom_job = manager.set_job('echo "foo"', ['*', '*', '*', '*', '*'])
    assert manager.get_job(command='echo "foo"')

    assert custom_job.script_name == None  # Coverage
    assert not custom_job.is_running()  # Coverage

    manager.disable_job(script_job)
    assert not script_job.enabled

    manager.enable_job(script_job)
    assert script_job.enabled

    manager.toggle_job(script_job)
    assert not script_job.enabled

    assert manager.get_job_logs(script_job) == []  # Create file
    assert manager.get_job_logs(script_job) == []  # Read file
    assert manager.get_job_logs(custom_job) == []  # No logs

    manager.remove_job(script_job)
    assert script_job not in manager.get_jobs()

    with pytest.raises(ValueError):
        manager.set_script_job('unexistent_script', ['*', '*', '*', '*', '*'])

    shutil.rmtree(f'{os.path.abspath("./python_scs")}/scripts')
    os.remove(f'{os.path.abspath("./python_scs")}/test_cronfile')
