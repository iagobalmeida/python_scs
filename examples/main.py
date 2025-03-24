from python_scs import PythonScriptsCronManager, streamlit_ui

manager = PythonScriptsCronManager(
    user=True
)

streamlit_pannel = streamlit_ui.init(
    manager,
    layout='wide',
    title='Scripts Manager',
    subheader='Manage your python scripts'
)

# To run: streamlit run main.py
