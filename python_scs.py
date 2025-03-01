import datetime
import os
import re
import subprocess
from dataclasses import dataclass
from logging import INFO, getLogger
from typing import List

import psutil
import streamlit as st
from crontab import CronTab


class PythonCronItem:
    def __init__(self, cron_item):
        self._cron_item = cron_item

    def __getattr__(self, name):
        if name not in {'script_name', 'is_running'}:
            return getattr(self._cron_item, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def script_name(self):
        match = re.search(r'\.([a-zA-Z_][a-zA-Z0-9_]*)\s*>>', self.command)
        return match.group(1) if match else self.command

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

    def set_job(self, script_name: str, schedule: List[str], comment: str = None, enable: bool = True) -> PythonCronItem:
        '''Cria um novo agendamento'''
        command = f'cd {self.app_path} && python3 -m {self.scripts_folder}.{script_name}'
        log_file = f'{self.logs_folder}/{script_name}.txt'
        job = PythonCronItem(self.crontab.new(command=f'{command} >> {log_file} 2>> {log_file}'))
        job.set_comment(comment or script_name)
        job.setall(' '.join(schedule))
        job.enable(enabled=enable)
        self.crontab.write()
        return job

    def get_scripts(self) -> List[str]:
        '''Retorna todos os scripts disponíveis na pasta de scripts'''
        return [file for file in os.listdir(f'{self.app_path}/{self.scripts_folder}') if file.endswith('.py') and file != '__init__.py']

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
        self.crontab.remove(job)
        self.crontab.write()

    def get_job_logs(self, job: PythonCronItem, lines: int = 20) -> List[str]:
        '''Retorna as últimas `lines` linhas do log de um agendamento'''
        log_file_path = f'{self.app_path}/{job.command.split(">>")[-1].strip()}'
        try:
            log_file = open(log_file_path, 'r+')
            return log_file.readlines()[-lines:]
        except FileNotFoundError:
            log_file = open(log_file_path, 'w+')
            return log_file.readlines()[-lines:]

    def streamlit_pannel(self, config: PannelConfig = PannelConfig()):
        '''Gera um painel em Streamlit para gerenciar agendamentos'''
        jobs, scripts = self.get_jobs(), self.get_scripts()
        st.set_page_config(layout=config.layout)

        st.title(config.title)
        st.text(config.subheader)

        st.divider()

        header_1, header_2, header_3 = st.columns(3)
        header_1.metric('Horário Atual', datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S"))
        header_2.metric('Scripts', len(scripts))
        header_3.metric('Agendamentos', len(jobs))

        st.divider()

        def st_dict_card(values: dict, col_sizes=[1, 2, 8]):
            '''Desenha um container com borda para exibir informações formatadas'''
            with st.container(border=True):
                for key, value in values.items():
                    cols = st.columns(col_sizes)
                    cols[0].write(f'**{key}**')
                    cols[1].write(str(value))

        @st.dialog('❔ Confirmar ação')
        def st_dialog_confirmar_acao(acao: str, descricao: str, **kwargs):
            '''Caixa de diálogo para confirmação de ações'''
            st.write(descricao)
            if acao == 'adicionar':
                st_dict_card({
                    'Script': f"`{kwargs['script_selecionado']}.py`",
                    'Habilitado': '✔ Sim' if kwargs['habilitado'] else '✖ Não',
                    'Comentário': kwargs['comentario'] or '_Não preenchido_',
                    'Agendamento': f"`{' '.join(kwargs['agendamento'])}`"
                }, col_sizes=[1, 2])

            if acao == 'executar':
                sincrono = st.toggle('Execução síncrona')

            if st.button('Confirmar ação'):
                if acao == 'executar':
                    self.execute_job(kwargs.get('job'), use_subprocess=not sincrono)
                elif acao == 'toggle':
                    self.toggle_job(kwargs.get('job'))
                elif acao == 'remover':
                    self.remove_job(kwargs.get('job'))
                elif acao == 'adicionar':
                    self.set_job(kwargs['script_selecionado'], kwargs['agendamento'].split(), kwargs['comentario'])
                st.rerun()

        with st.expander('Adicionar novo agendamento', icon='📜'):
            script_selecionado = st.selectbox('Selecione um script', options=scripts)
            script_selecionado = script_selecionado.split('.')[0]
            agendamento = st.text_input('Agendamento', value='* * * * *')
            comentario = st.text_input('Comentário', value='')
            habilitado = st.toggle('Habilitado', value=True)
            if st.button('Adicionar'):
                st_dialog_confirmar_acao(
                    'adicionar',
                    'Deseja agendar o script?',
                    script_selecionado=script_selecionado,
                    agendamento=agendamento,
                    comentario=comentario,
                    habilitado=habilitado
                )

        for job in jobs:
            proxima_execucao = job.schedule().get_next().strftime("%d/%m/%Y às %H:%M:%S")
            expander_icon = "✔" if job.enabled else "✖"
            with st.expander(f'**{job.comment or job.script_name}** {" - " + proxima_execucao if job.enabled else ""}', icon=expander_icon, expanded=True):
                st.subheader(job.comment or job.script_name)
                if job.is_running():
                    st.success('Este serviço está rodando')
                col1, col2, col3, space = st.columns([1, 1, 1, 8])
                if col1.button('Executar', icon='⚙'):
                    st_dialog_confirmar_acao('executar', 'Deseja executar de forma síncrona esse agendamento?', job=job)
                if col2.button('Habilitar' if not job.enabled else 'Desabilitar', icon='✔' if not job.enabled else '✖'):
                    st_dialog_confirmar_acao('toggle', f'Deseja {"habilitar" if not job.enabled else "desabilitar"} esse agendamento?', job=job)
                if col3.button('Remover', icon='🗑'):
                    st_dialog_confirmar_acao('remover', 'Deseja remover esse agendamento?', job=job)
                st_dict_card({
                    'Script': f'`{job.script_name}.py`',
                    'Habilitado': '✔ Sim' if job.enabled else '✖ Não',
                    'Comentário': job.comment or '_Não preenchido_',
                    'Agendamento': f'`{" ".join(job.schedule().expressions)}`',
                    'Próxima execução': proxima_execucao,
                })
                st.subheader('Logs')
                logs = self.get_job_logs(job)
                st.code(''.join(logs) if logs else 'Nenhum log disponível')
