import datetime
import os
import re
import subprocess
from dataclasses import dataclass
from logging import INFO, getLogger
from typing import List
from uuid import uuid4

import psutil
import streamlit as st
from crontab import CronItem, CronTab


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

    def get_job_by_script_name(self, script_name: str) -> PythonCronItem:
        '''Retorna um agendamento com base no nome do script'''
        for job in self.get_jobs():
            if job.script_name == script_name:
                return job
        raise ValueError(f"No job found for script name: {script_name}")

    def get_job_by_command(self, command: str) -> PythonCronItem:
        '''Retorna um agendamento com base no comando'''
        for job in self.get_jobs():
            if job.command == command:
                return job
        raise ValueError(f"No job found for command: {command}")

    def set_job(self, command: str, schedule: List[str], comment: str = None, enable: bool = True) -> PythonCronItem:
        '''Cria um novo agendamento'''
        cron_item = self.crontab.new(command=command)
        job = PythonCronItem(cron_item)
        if comment:
            job.set_comment(comment)
        job.setall(' '.join(schedule))
        job.enable(enabled=enable)
        self.crontab.write()
        return job

    def set_script_job(self, script_name: str, schedule: List[str], comment: str = None, enable: bool = True) -> PythonCronItem:
        '''Cria um novo agendamento'''
        command = f'cd {self.app_path} && python3 -m {self.scripts_folder}.{script_name}'
        log_file = f'{self.logs_folder}/{script_name}_{uuid4()}.txt'
        return self.set_job(
            command=f'{command} >> {log_file} 2>> {log_file}',
            schedule=schedule,
            comment=comment,
            enable=enable
        )

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
        try:
            with open(log_file_path, 'r+') as log_file:
                return log_file.readlines()[-lines:]
        except FileNotFoundError:
            with open(log_file_path, 'w+') as log_file:
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

        def st_dict_card(values: dict, col_sizes=[1, 10]):
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
                dict = {
                    'Habilitado': '✔ Sim' if kwargs['habilitado'] else '✖ Não',
                    'Comentário': kwargs['comentario'] or '_Não preenchido_',
                    'Agendamento': f"`{' '.join(kwargs['agendamento'])}`"
                }
                if kwargs.get('comando_customizado', False):
                    dict['Comando Customizado'] = f"`{kwargs['comando_customizado']}`"
                else:
                    dict['Script'] = kwargs['script_selecionado']
                st_dict_card(dict, col_sizes=[1, 2])

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
                    if kwargs['comando_customizado']:
                        self.set_job(
                            command=kwargs['comando_customizado'],
                            schedule=kwargs['agendamento'].split(),
                            comment=kwargs['comentario'],
                            enable=kwargs['habilitado']
                        )
                    else:
                        self.set_script_job(
                            script_name=kwargs['script_selecionado'],
                            schedule=kwargs['agendamento'].split(),
                            comment=kwargs['comentario'],
                            enable=kwargs['habilitado']
                        )
                st.rerun()

        with st.expander('Adicionar novo agendamento', icon='📜'):
            script_selecionado = st.selectbox('Selecione um script', options=[*scripts, 'Comando customizado'])
            script_selecionado = script_selecionado.split('.')[0]
            comando_customizado = None
            if script_selecionado == 'Comando customizado':
                comando_customizado = st.text_input('Comando')
            agendamento = st.text_input('Agendamento', value='* * * * *')
            comentario = st.text_input('Comentário', value='')
            habilitado = st.toggle('Habilitado', value=True)
            if st.button('Adicionar'):
                st_dialog_confirmar_acao(
                    'adicionar',
                    'Deseja agendar o script?',
                    script_selecionado=script_selecionado,
                    comando_customizado=comando_customizado,
                    agendamento=agendamento,
                    comentario=comentario,
                    habilitado=habilitado
                )

        for job_index, job in enumerate(jobs):
            proxima_execucao = job.schedule().get_next().strftime("%d/%m/%Y às %H:%M:%S")
            expander_icon = "✔" if job.enabled else "✖"
            with st.expander(f'**{job.comment or job.script_name}** {" - " + proxima_execucao if job.enabled else ""}', icon=expander_icon, expanded=True):
                st.subheader(job.comment or job.script_name)
                if job.is_running():
                    st.success('Este comando está sendo executado')
                col1, col2, col3, space = st.columns([1, 1, 1, 8])
                if col1.button('Executar', icon='⚙', key=f'executar_{job_index}'):
                    st_dialog_confirmar_acao('executar', 'Deseja executar de forma síncrona esse agendamento?', job=job)
                if col2.button('Habilitar' if not job.enabled else 'Desabilitar', icon='✔' if not job.enabled else '✖', key=f'habilitar_{job_index}'):
                    st_dialog_confirmar_acao('toggle', f'Deseja {"habilitar" if not job.enabled else "desabilitar"} esse agendamento?', job=job)
                if col3.button('Remover', icon='🗑', key=f'remover_{job_index}'):
                    st_dialog_confirmar_acao('remover', 'Deseja remover esse agendamento?', job=job)
                st_dict_card({
                    'Script': f'`{job.script_name}.py`',
                    'Habilitado': '✔ Sim' if job.enabled else '✖ Não',
                    'Comentário': job.comment or '_Não preenchido_',
                    'Agendamento': f'`{" ".join(job.schedule().expressions)}`',
                    'Arquivo de Logs': f'`{self.get_job_log_file_path(job)}.txt`',
                    'Próxima execução': proxima_execucao,
                    'Comando': f'`{job.command}`'
                })
                st.subheader('Logs')
                logs = self.get_job_logs(job)
                st.code(''.join(logs) if logs else 'Nenhum log disponível')
