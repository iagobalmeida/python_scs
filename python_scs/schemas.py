import re
from dataclasses import dataclass

import psutil
from crontab import CronItem


class PythonCronItem:
    def __init__(self, cron_item: CronItem):
        self._cron_item = cron_item

    def __getattr__(self, name):
        if name not in {'script_name', 'is_running'}:
            return getattr(self._cron_item, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def script_name(self):
        match = re.search(r'\.([a-zA-Z_][a-zA-Z0-9_]*)\s*>>', self.command)
        return match.group(1) if match else None

    def is_running(self):
        for proc in psutil.process_iter(attrs=['cmdline']):
            try:
                cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                if self.command in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False


@dataclass
class PannelConfig:
    layout: str = 'wide'
    title: str = 'Crontab Interface'
    subheader: str = 'Interface para gerenciamento de agendamentos'
    allow_upload_script: bool = True
    allow_create_job: bool = True
    allow_execute_job: bool = True
    allow_toggle_job: bool = True
    allow_remove_job: bool = True
