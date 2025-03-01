import os

from python_scs import PannelConfig, PythonScriptsCronManager

scripts_manager = PythonScriptsCronManager(
    config=PythonScriptsCronManager.Config(
        app_path=os.path.abspath('.'),  # Raiz onde scripts_folder estará
        scripts_folder='scripts',       # Diretório com os códigos
        logs_folder='scripts/logs'      # Diretório de logs
    ),
    user=True
)

scripts_manager.streamlit_pannel(config=PannelConfig(
    layout='wide',
    title='Crontab Interface',
    subheader='Interface para gerenciamento de agendamentos'
))
