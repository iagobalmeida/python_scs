import os
import subprocess
from logging import INFO, getLogger
from typing import List, Union
from uuid import uuid4

from crontab import CronTab

from .schemas import PythonCronItem


class PythonScriptsCronManager:
    '''PythonScriptsCronManager object allows managing the execution of CRON Jobs, abstracting output configuration and python scripts execution.'''

    def __init__(self, app_path: str = None, scripts_folder: str = None, logs_folder: str = None, crontab_tabfile: str = None, crontab_log: str = None, user=None, log_level: int = INFO) -> None:
        if not app_path:  # pragma: nocover
            app_path = os.path.abspath('.')

        if not scripts_folder:
            scripts_folder = '/scripts'

        if not logs_folder:
            logs_folder = '/scripts/logs'

        if crontab_tabfile:
            crontab_tabfile = f'{app_path}{crontab_tabfile}'

        self.app_path = app_path
        self.scripts_folder = scripts_folder
        self.logs_folder = logs_folder
        self.crontab_tabfile = crontab_tabfile

        self.__check_folders()

        self.log = getLogger(__name__)
        self.log.setLevel(log_level)

        self.crontab = CronTab(
            user=user,
            tabfile=crontab_tabfile,
            log=crontab_log
        )

    def __check_folders(self):
        os.makedirs(f'{self.app_path}/{self.scripts_folder}', exist_ok=True)
        os.makedirs(f'{self.app_path}/{self.logs_folder}', exist_ok=True)

    def clear_jobs(self) -> List[PythonCronItem]:
        '''Removes all the jobs'''
        self.crontab.remove_all()
        self.crontab.write(self.crontab_tabfile)

    def get_jobs(self) -> List[PythonCronItem]:
        '''Returns all the `PythonCronItem`'s configured in the CRON file.'''
        self.crontab.read(self.crontab_tabfile)
        return [
            PythonCronItem(
                command=job.command,
                comment=job.comment,
                user=job.user,
                pre_comment=job.pre_comment
            )
            for job in self.crontab
        ]

    def get_job(self, script_name: str = None, comment: str = None, command: str = None, marker: str = None) -> Union[PythonCronItem, None]:
        '''Returns a specific job configured in the CRON file according to the `filters` criteria.'''
        for job in self.get_jobs():
            if script_name and not script_name in job.script_name:
                continue
            if command and not job.command == command:
                continue
            if comment and not job.comment == comment:
                continue
            if marker and not job.marker == marker:
                continue
            return job
        return None

    def set_job(self, command: str, schedule: List[str], log_file_name: str = None, comment: str = None, enable: bool = True) -> PythonCronItem:
        '''Creates and insert into the CRON file a new `PythonCronItem` that executes a command.'''
        if log_file_name:
            log_file_path = f'{self.logs_folder}/{log_file_name}'
            command = f'{command} &>> {log_file_path}'
        cron_job = self.crontab.new(
            command=command,
            comment=comment,
            user=self.crontab.user
        )
        job = PythonCronItem(cron_job.command, cron_job.comment, cron_job.user, cron_job.pre_comment)
        job.cron = cron_job.cron
        if comment:
            job.set_comment(comment)
        job.setall(' '.join(schedule))
        job.enable(enabled=enable)
        self.crontab.write(self.crontab_tabfile)
        return job

    def set_script_job(self, script_name: str, schedule: List[str], log_file_name: str = None, comment: str = None, enable: bool = True) -> PythonCronItem:
        '''Creates and insert into the CRON a new `PythonCronItem` that executes a python script. Raises `ValueError` if script is not found.'''
        if not script_name in self.get_scripts():
            raise ValueError(f'{script_name} not found.')
        return self.set_job(
            command=f'cd {self.app_path} && python3 -m {self.scripts_folder}.{script_name}',
            schedule=schedule,
            log_file_name=log_file_name if log_file_name else f'{script_name}_{uuid4()}.text',
            comment=comment,
            enable=enable
        )

    def get_scripts(self) -> List[str]:
        '''Returns the `.py` scripts in the `scripts_folder`.'''
        return [file for file in os.listdir(f'{self.app_path}/{self.scripts_folder}') if file.endswith('.py') and file != '__init__.py']

    def upload_script(self, file_name: str, file_bytes: bytes):
        '''Creates a new `.py` script in the `scripts_folder`.'''
        if not '.py' in file_name:
            file_name = f"{file_name}.py"
        file_path = f"{self.app_path}/{self.scripts_folder}/{file_name}"
        with open(file_path, 'wb') as file:
            file.write(file_bytes)

    def enable_job(self, job: PythonCronItem):
        '''Enable a `PythonCronItem` configured in the CRON file.'''
        job.enable(True)
        self.crontab.write(self.crontab_tabfile)
        return job.enabled

    def disable_job(self, job: PythonCronItem):
        '''Disable a `PythonCronItem` configured in the CRON file.'''
        job.enable(False)
        self.crontab.write(self.crontab_tabfile)
        return job.enabled

    def toggle_job(self, job: PythonCronItem):
        '''Enable/Disable a `PythonCronItem` configured in the CRON file.'''
        return self.disable_job(job) if job.enabled else self.enable_job(job)

    def execute_job(self, job: PythonCronItem, use_subprocess: bool = False) -> subprocess.Popen:  # pragma: nocover
        '''Execute a `PythonCronItem`. If `use_subprocess=True` will create and return a `subprocess.Popen`, else will return the Job output.'''
        if use_subprocess:
            return subprocess.Popen(job.command, shell=True)
        return job.run()

    def remove_job(self, job: PythonCronItem) -> None:
        '''Removes a `PythonCronItem` from the CRON file.'''
        self.crontab.remove(job)
        self.crontab.write(self.crontab_tabfile)

    def get_job_log_file_path(self, job: PythonCronItem):
        '''Returns the path to `PythonCronItem` the log file.'''
        if not '&>>' in job.command:
            return None
        return f'{self.app_path}/{job.command.split("&>>")[-1].strip()}'

    def get_job_logs(self, job: PythonCronItem, lines: int = 20) -> List[str]:
        '''Returns the last `lines` lines of the `PythonCronItem`.'''
        log_file_path = self.get_job_log_file_path(job)
        if not log_file_path:
            return []

        directory = os.path.dirname(log_file_path)
        if not os.path.isdir(directory):  # pragma: no cover
            raise FileNotFoundError(f'Diretório de logs "{directory}" não encontrado')
        try:
            with open(log_file_path, 'r+') as log_file:
                return log_file.readlines()[-lines:]
        except FileNotFoundError:
            with open(log_file_path, 'w+') as log_file:
                return log_file.readlines()[-lines:]
