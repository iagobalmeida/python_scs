from logging import getLogger

from modules.db import DBInterface
from modules.python_crontab import PythonCrontrabInterface

log = getLogger(__name__)


def main():
    crontab_interface = PythonCrontrabInterface()
    crontab_interface.get_jobs(log_details=True)


if __name__ == '__main__':
    main()
