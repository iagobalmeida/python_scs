import re
from dataclasses import dataclass

import psutil
from crontab import CronItem


class PythonCronItem(CronItem):
    @property
    def script_name(self):
        if '.py' in self.command:
            match = re.search(r'python3\s+-m\s+[^/]*\/([^ ]+)', self.command)
            return match.group(1) if match else None
        return None

    def is_running(self) -> bool:
        running = False
        try:
            for proc in psutil.process_iter(attrs=['cmdline']):
                cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                running = self.command in cmdline
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):  # pragma: no cover
            pass
        finally:
            return running


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
