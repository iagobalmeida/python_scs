import os

from python_scs import PythonScriptsCronManager
from python_scs.streamlit_ui import PannelConfig, StreamlitPannel

scripts_manager = PythonScriptsCronManager(
    config=PythonScriptsCronManager.Config(
        app_path=os.path.abspath('.'),  # Raiz onde scripts_folder estará
        scripts_folder='scripts',       # Diretório com os códigos
        logs_folder='scripts/logs'      # Diretório de logs
    ),
    user=True
)

streamlit_pannel = StreamlitPannel(scripts_manager, config=PannelConfig(
    layout='wide',
    title='Crontab Interface',
    subheader='Interface para gerenciamento de agendamentos',
    allow_upload_script=True,
    allow_create_job=True,
    allow_execute_job=True,
    allow_toggle_job=True,
    allow_remove_job=True
))
