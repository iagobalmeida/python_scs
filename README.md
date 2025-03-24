# Python Scripts Cron Scheduler

**Abstraction for managing the scheduling of Python scripts through CronJobs with a out-of-the-box Streamlit Panel.**

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Linux](https://img.shields.io/badge/Linux-222222.svg?style=for-the-badge&logo=linux&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-%23FE4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)

[![Tests Status](./reports/tests-badge.svg?dummy=8484744)](./reports/junit/report.html)
[![Coverage Status](./reports/coverage-badge.svg?dummy=8484744)](./reports/htmlcov/report.html)

## 📌 Installation

```bash
pip install python_scs
```

If you want to use the Streamlit panel:
```bash
pip install python_scs[streamlit]
```

## 🚀 Configuration

Check out the [full example](https://github.com/iagobalmeida/python_scs/tree/master/examples).

1. Make sure you have the following directory structure:

```
├── scripts/
│   ├── logs/
│   ├── script_test.py
│   ├── __init__.py
├── streamlit_pannel.py
```

2. Instantiate the script manager and configure the panel:

```python
# streamlit_pannel.py
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
```

3. Run the panel using `streamlit`:

```bash
streamlit run streamlit_pannel.py
```

## 🛠 Using the API

### Instantiating the script manager

```python
import os
from python_scs import PythonScriptsCronManager

scripts_manager = PythonScriptsCronManager(
    config=PythonScriptsCronManager.Config(
        app_path=os.path.abspath("."),  # Root directory where scripts_folder is located
        scripts_folder="scripts",       # Directory containing scripts
        logs_folder="scripts/logs"      # Directory for logs
    ),
    user=True
)
```

📌 *Check the [python-crontab documentation](https://pypi.org/project/python-crontab/#how-to-use-the-module) to understand the `user` parameter.*

### Listing available scripts

```python
scripts = scripts_manager.get_scripts()
print(scripts)  # ["script_test.py"]
```

### Creating a schedule

```python
job = scripts_manager.set_script_job(
    script_name="script_test.py",
    schedule=["* * * * *"],
    comment="Test schedule",
    enable=True
)

# Creating a schedule with a custom UNIX command
job = scripts_manager.set_job(
    command='echo "Teste"',
    schedule=["* * * * *"],
    log_file_name="test.txt",  # Required to store output
    comment="Custom schedule",
    enable=True
)
```

📌 To verify if the schedule was created, run:
```bash
crontab -l
```

### Listing configured schedules

```python
jobs = scripts_manager.get_jobs()
for job in jobs:
    print(f"{job.comment} - {job.script_name} - {job.is_runing()}")

# Fetching a scheduled job by filters
job_script_test = scripts_manager.get_job({
    "script_name": "script_test.py",
    "comment": "Test schedule"
})
```

### Enabling, disabling, executing, and removing a scheduled job

```python
job = scripts_manager.get_job({
    "script_name": "script_test.py",
    "comment": "Test schedule"
})

job.enable_job()     # Enables the job
job.disable_job()    # Disables the job
job.toggle_job()     # Toggles between enabled/disabled

# Manually execute the script
scripts_manager.execute(job)

# Execute as a subprocess
scripts_manager.execute(job, use_subprocess=True)

# Remove the schedule
scripts_manager.remove_job(job)
```

## 📜 License

This project is distributed under the MIT license. See the [LICENSE](./LICENSE) file for more details.

