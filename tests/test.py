import time
from logging import getLogger

from modules.db import DBInterface
from modules.python_crontab import PythonCrontrabInterface

log = getLogger(__name__)
db_interface = DBInterface()
crontab_interface = PythonCrontrabInterface(user='visie')


def test_set_cronjobs():
    log.info('Gettings jobs from DB...')
    db_jobs = db_interface.get_cron_jobs()
    log.info(f'{len(db_jobs)} jobs found.')
    log.info('Syncing with crontab...')
    crontab_interface.set_jobs(db_jobs)
    cron_jobs = crontab_interface.get_jobs(log_details=True)
    log.info(f'{len(cron_jobs)} configured.')
