from python_scs.core import PythonScriptsCronManager
from python_scs.streamlit_ui import init

manager = PythonScriptsCronManager(crontab_tabfile='/teste')
init(manager)
