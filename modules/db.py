from typing import List

from modules.python_crontab import CronJob, PythonCrontrabInterface


class DBInterface():
    def __init__(self) -> None:
        self.registers = {
            'scripts': [
                [
                    'teste',
                    'gerar_erro',
                    '*/1 * * * *',
                ],
                [
                    'teste',
                    'gerar_sucesso',
                    '*/1 * * * *',
                ],
            ]
        }
        pass

    def get_cron_jobs(self, marker: str = None) -> List[CronJob]:
        def __to_CronJob(register: List[str]) -> CronJob:
            return PythonCrontrabInterface.cron_job(
                marker=register[0],
                comment=register[1],
                schedule=register[2].split()
            )
        return [
            __to_CronJob(register)
            for register in self.registers['scripts']
            if register[0] == marker or marker == None
        ]
