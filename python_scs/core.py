import os
import subprocess
from dataclasses import dataclass
from logging import INFO, getLogger
from typing import List
from uuid import uuid4

from crontab import CronTab

from .schemas import PythonCronItem


class PythonScriptsCronManager:
    '''Módulo para gestão da execução de scripts em Python via cron'''

    @dataclass
    class Config:
        app_path: str = os.path.abspath('.')
        scripts_folder: str = 'scripts'
        logs_folder: str = 'scripts/logs'

    def __init__(self, config: Config = Config(), user=None, log_level: int = INFO) -> None:
        self.crontab = CronTab(user=user)
        self.app_path = config.app_path
        self.scripts_folder = config.scripts_folder
        self.logs_folder = config.logs_folder
        self.log = getLogger(__name__)
        self.log.setLevel(log_level)

    def get_jobs(self) -> List[PythonCronItem]:
        '''Retorna todos os agendamentos configurados'''
        self.crontab.read()
        return [PythonCronItem(job) for job in self.crontab]

    def get_job(self, filters: dict) -> PythonCronItem:
        '''Retorna o primeiro agendamento encontrado que bate com os filtros'''
        for job in self.get_jobs():
            if all([
                getattr(job, key) == value
                for key, value in filters.items()
            ]):
                return job
        raise ValueError(f"No job found with filters: {filters}")

    def set_job(self, command: str, schedule: List[str], log_file_name: str = None, comment: str = None, enable: bool = True) -> PythonCronItem:
        '''Cria um novo agendamento'''
        if log_file_name:
            log_file_path = f'{self.logs_folder}/{log_file_name}'
            command = f'{command} >> {log_file_path} 2>> {log_file_path}'
        cron_item = self.crontab.new(command=command)
        job = PythonCronItem(cron_item)
        if comment:
            job.set_comment(comment)
        job.setall(' '.join(schedule))
        job.enable(enabled=enable)
        self.crontab.write()
        return job

    def set_script_job(self, script_name: str, schedule: List[str], log_file_name: str = None, comment: str = None, enable: bool = True) -> PythonCronItem:
        '''Cria um novo agendamento'''
        return self.set_job(
            command=f'cd {self.app_path} && python3 -m {self.scripts_folder}.{script_name}',
            schedule=schedule,
            log_file_name=log_file_name if log_file_name else f'{script_name}_{uuid4()}.text',
            comment=comment,
            enable=enable
        )

    def get_scripts(self) -> List[str]:
        '''Retorna todos os scripts disponíveis na pasta de scripts'''
        return [file for file in os.listdir(f'{self.app_path}/{self.scripts_folder}') if file.endswith('.py') and file != '__init__.py']

    def upload_script(self, file_name: str, file_bytes: bytes):
        if not '.py' in file_name:
            file_name = f"{file_name}.py"
        file_path = f"{self.app_path}/{self.scripts_folder}/{file_name}"
        with open(file_path, 'wb') as file:
            file.write(file_bytes)

    def toggle_job(self, job: PythonCronItem):
        '''Habilita/desabilita um agendamento'''
        job.enable(not job.enabled)
        self.crontab.write()
        return job.enabled

    def execute_job(self, job: PythonCronItem, use_subprocess: bool = False) -> str:
        '''Executa um agendamento imediatamente'''
        if use_subprocess:
            subprocess.Popen(job.command, shell=True)
            return 'ok'
        return job.run()

    def remove_job(self, job: PythonCronItem) -> None:
        '''Remove um agendamento'''
        self.crontab.remove(job._cron_item)
        self.crontab.write()

    def get_job_log_file_path(self, job: PythonCronItem):
        if not '>>' in job.command:
            return None
        return f'{self.app_path}/{job.command.split(">>")[-1].strip()}'

    def get_job_logs(self, job: PythonCronItem, lines: int = 20) -> List[str]:
        '''Retorna as últimas `lines` linhas do log de um agendamento'''
        log_file_path = self.get_job_log_file_path(job)
        if not log_file_path:
            return []

        directory = os.path.dirname(log_file_path)
        if not os.path.isdir(directory):
            raise FileNotFoundError(f'Diretório de logs "{directory}" não encontrado')
        try:
            with open(log_file_path, 'r+') as log_file:
                return log_file.readlines()[-lines:]
        except FileNotFoundError:
            with open(log_file_path, 'w+') as log_file:
                return log_file.readlines()[-lines:]
