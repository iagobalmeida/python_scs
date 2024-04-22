import os
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from typing import List

from croniter.croniter import croniter
from crontab import CronItem, CronTab

log = getLogger(__name__)


def __abspath(path: str) -> str:
    return os.path.abspath(path)


def logs_path(file_name: str) -> str:
    return __abspath(f'./scripts/logs/{file_name}')


def app_path() -> str:
    return __abspath(f'.')


@dataclass
class CronJob():
    '''Abstração de um trabalho cron.'''
    marker: str
    comment: str
    command: str
    schedule: List[str]
    log_file: str

    def to_line(self) -> str:
        '''Gera a linha a ser escrita no arquivo de configuração referente a esse trabalho.'''
        if self.marker:
            comment = f'#{self.marker}: {self.comment}'
        else:
            comment = f'#{self.comment}'
        return f'{" ".join(self.schedule)} {self.command} {comment}'


class PythonCrontrabInterface():
    '''Módulo para gestão da execução de scripts em Python via cron a partir de um banco de dados'''

    def __init__(self, user: str) -> None:
        self.crontab = CronTab(user=user)
        pass

    @classmethod
    def cron_job(self, marker: str, comment: str, schedule: List[str]) -> CronJob:
        '''Factory para uma entidade `CronJob`'''
        app_folder_path = app_path()

        command = f'cd {app_folder_path} && python3 -m scripts.{comment}'

        log_file_name = f'{comment}.txt'
        log_file = logs_path(log_file_name)

        full_command = f'{command} >> {log_file} 2>> {log_file}'

        return CronJob(
            marker=marker,
            comment=comment,
            command=full_command,
            schedule=schedule,
            log_file=log_file
        )

    def get_jobs(self, log_details=False) -> List[CronJob]:
        '''Retorna todos os trabalhos configurados na máquina, loga em nível `INFO` caso `log_details=True`.'''
        def __to_CronJob(job: CronItem) -> CronJob:
            schedule: croniter = job.schedule(date_from=datetime.now())

            command_split = job.command.split('2>>')
            command_split = command_split[0].split('>>')
            log_file = command_split[1] if len(command_split) > 1 else None

            ret = CronJob(
                marker=job.marker,
                comment=job.comment,
                command=job.command,
                log_file=log_file,
                schedule=schedule.expressions
            )
            if log_details:
                log.info(f'{job.comment}')
                log.info(ret)
                log.info(f'Enabled: {job.enabled}')
                log.info(f'Next: {schedule.next()}')
                log.info('\n')
            return ret
        return [
            __to_CronJob(job) for job in self.crontab
        ]

    def set_job(self, job: CronJob, enable: bool = True) -> CronItem:
        '''Configura um trabalho na máquina.'''
        job_line = job.to_line()
        log.info(f'Creating from line: "{job_line}"')
        _job = CronItem.from_line(line=job_line, user=self.crontab.user, cron=self.crontab)
        _job.comment = job.comment
        _job.marker = job.marker
        _job.enable(enabled=enable)
        self.crontab.append(_job)
        self.crontab.write()
        return _job

    def set_jobs(self, jobs: List[CronJob], enable: bool = True) -> None:
        '''Apaga os trabalhos configurados e configura uma lista de trabalhos na máquina.'''
        self.crontab.remove_all()
        for job in jobs:
            self.set_job(job=job, enable=enable)
