import os
import shutil

from .core import PythonScriptsCronManager
from .streamlit_ui import init

# from streamlit.testing.v1 import AppTest


def test_streamlit_ui():
    with open(f'{os.path.abspath("./python_scs")}/test_cronfile', 'w+') as cron_file:
        pass

    manager = PythonScriptsCronManager(
        app_path=os.path.abspath('./python_scs'),
        crontab_tabfile='/test_cronfile'
    )

    manager.set_job('Echo "teste"', ['*', '*', '*', '*', '*'])
    init(manager)

    # pannel = AppTest.from_function(script=init, args=[manager])
    # pannel.run()

    shutil.rmtree(f'{os.path.abspath("./python_scs")}/scripts')
    os.remove(f'{os.path.abspath("./python_scs")}/test_cronfile')
