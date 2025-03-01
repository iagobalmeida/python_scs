import os
import re
from dataclasses import dataclass
from datetime import datetime
from logging import INFO, getLogger
from typing import List

import psutil
from crontab import CronItem, CronTab


@dataclass
class PannelConfig():
    layout: str = 'wide'
    title: str = 'Crontab Interface'
    subheader: str = 'Interface para gerenciamento de agendamentos'


class PythonCronItem:
    def __init__(self, cron_item: CronItem):
        self._cron_item = cron_item

    @classmethod
    def from_cron_item(cls, cron_item: CronItem):
        return cls(cron_item)

    def __getattr__(self, name):
        if name not in {'script_name', 'is_running'}:
            return getattr(self._cron_item, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def script_name(self):
        match = re.search(r'\.([a-zA-Z_][a-zA-Z0-9_]*)\s*>>', self.command)
        if match:
            return match.group(1)
        return self.command

    def is_running(self):
        for proc in psutil.process_iter(attrs=['cmdline']):
            try:
                cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                if self.command in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False


class PythonScriptsCronManager():
    '''Módulo para gestão da execução de scripts em Python via cron'''
    app_path: str
    scripts_folder: str

    @dataclass
    class Config():
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
        pass

    def get_jobs(self) -> List[PythonCronItem]:
        '''Retorna todos os agendamentos configurados'''
        self.crontab.read()
        return [
            PythonCronItem(job) for job in self.crontab
        ]

    def set_job(self, script_name: str, schedule: List[str], comment: str = None, enable: bool = True) -> PythonCronItem:
        '''Factory para uma entidade `CronItem`'''

        script_path = self.scripts_folder
        command = f'cd {self.app_path} && python3 -m {script_path}.{script_name}'

        log_file_name = f'{script_name}.txt'
        log_file = f'{self.logs_folder}/{log_file_name}'

        job = PythonCronItem(self.crontab.new(
            command=f'{command} >> {log_file} 2>> {log_file}'
        ))

        job.set_comment(comment if comment else script_name)
        job.setall(' '.join(schedule))
        job.enable(enabled=enable)

        self.crontab.write()
        return job

    def get_scripts(self) -> List[str]:
        '''Retorna todos os scripts disponíveis na pasta de scripts'''
        scripts = []
        for root, dirs, files in os.walk(f'{self.app_path}/{self.scripts_folder}'):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    scripts.append(file)
        return scripts

    def enable_job(self, job: PythonCronItem):
        job.enable(True)
        print('enable_job')
        self.crontab.write()
        return True

    def disable_job(self, job: PythonCronItem):
        job.enable(False)
        print('disable_job')
        self.crontab.write()
        return False

    def toggle_job(self, job: PythonCronItem):
        '''Habilita/desabilita um agendamento'''
        return self.enable_job(job) if not job.enabled else self.disable_job(job)

    def execute_job(self, job: PythonCronItem) -> str:
        '''Executa um agendamento imediatamente de forma síncrona'''
        return job.run()

    def remove_job(self, job: PythonCronItem) -> None:
        '''Remove um agendamento da máquina.'''
        self.crontab.remove(job)
        self.crontab.write()

    def get_job_logs(self, job: PythonCronItem, lines: int = 20) -> List[str]:
        '''Retorna as últimas `lines` linhas do log de um agendamento'''
        log_file_name = job.command.split('>>')[-1].strip()
        log_file = f'{self.app_path}/{log_file_name}'
        try:
            log_file = open(log_file, 'r+')
            return log_file.readlines()[-lines:]
        except FileNotFoundError:
            log_file = open(log_file, 'w+')
            return log_file.readlines()[-lines:]

    def streamlit_pannel(self, config: PannelConfig = PannelConfig()):
        '''Gera um painel em Streamlit que permite gerenciar os agendamentos'''
        import streamlit as st
        jobs = self.get_jobs()
        scripts = self.get_scripts()

        def st_dict_card(values: dict):
            '''Desenha um container com borda com as chaves do dicionario'''
            with st.container(border=True):
                for key, value in values.items():
                    col_label, col_value, _ = st.columns([1, 2, 8])
                    col_label.write(f'**{key}**')
                    col_value.write(str(value))

        @st.dialog('Confirmar ação')
        def st_dialog_confirmar_acao(acao, **kwargs):
            if acao == 'executar' or acao == 'remover':
                st.write(f'Tem certeza que deseja {acao}?')
            elif acao == 'toggle':
                job = kwargs.get('job')
                st.write(f'Tem certeza que deseja {"desabilitar" if job.enabled else "habilitar"}?')
            elif acao == 'adicionar':
                script_selecionado = kwargs.get('script_selecionado')
                agendamento = kwargs.get('agendamento', '* * * * *')
                comentario = kwargs.get('comentario', None)
                st.write(f'Tem certeza que deseja adicionar agendamento de script?')
                st.write({'script': script_selecionado, 'agendamento': agendamento, 'comentário': comentario})

            if st.button('Confirmar ação'):
                if acao == 'executar':
                    job = kwargs.get('job')
                    st.toast('Executando...', icon='🤖')
                    self.execute_job(job)
                if acao == 'toggle':
                    job = kwargs.get('job')
                    self.toggle_job(job)
                elif acao == 'remover':
                    job = kwargs.get('job')
                    self.remove_job(job)
                elif acao == 'adicionar':
                    self.set_job(script_selecionado, agendamento.split(), comentario)
                st.rerun()

        st.set_page_config(
            layout=config.layout
        )
        st.title(config.title)
        st.text(config.subheader)

        st.divider()

        st.metric('Horário Atual', value=datetime.now().strftime("%d/%m/%Y ás %H:%M:%S"))

        with st.expander('Adicionar novo script'):
            script_selecionado = st.selectbox('Selecione um script', options=scripts)
            script_selecionado = script_selecionado.split('.')[0]
            agendamento = st.text_input('Agendamento', value='* * * * *')
            comentario = st.text_input('Comentário', value='')
            if st.button('Adicionar'):
                st_dialog_confirmar_acao('adicionar', script_selecionado=script_selecionado, agendamento=agendamento, comentario=comentario)

        for index in range(len(jobs)):
            job = jobs[index]
            running = job.is_running()
            expander_icon = '✔' if job.enabled else '✖'
            expander_sufix = '...' if running else ''
            expander_title = job.comment if job.comment else job.script_name
            with st.expander(f'**{expander_icon} - {expander_title}** {expander_sufix}', expanded=True):
                st.subheader(f'**{expander_title}**')

                if running:
                    st.success('Este serviço está rodando')

                col1, col2, col3, col4 = st.columns([1, 1, 1, 11])
                with col1:
                    if st.button('Executar', key=f'executar_{index}'):
                        st_dialog_confirmar_acao('executar', job=job)
                with col2:
                    toggle_title = 'Desabilitar' if job.enabled else 'Habilitar'
                    if st.button(toggle_title, key=f'toggle_{index}'):
                        st_dialog_confirmar_acao('toggle', job=job)
                with col3:
                    if st.button('Remover', key=f'remover_{index}'):
                        st_dialog_confirmar_acao('remover', job=job)

                st_dict_card({
                    'Código': f'`{job.script_name}.py`',
                    'Habilitado': 'Sim' if job.enabled else 'Não',
                    'Comentário': job.comment if job.comment else '_Não preenchido_',
                    'Agendamento': f'`{" ".join(job.schedule().expressions)}`',
                    'Próxima execução': job.schedule().get_next().strftime("%d/%m/%Y ás %H:%M:%S"),
                    'Última execução': job.last_run
                })

                st.code(job.command)

                st.subheader('Logs')
                with st.container(border=True):
                    logs = self.get_job_logs(job)
                    if not logs:
                        st.write('Nenhum log disponível')
                    else:
                        st.code(''.join(logs))
