import datetime
import re
from typing import List
from uuid import uuid4

import streamlit as st

from .schemas import PannelConfig, PythonCronItem


class StreamlitPannel:
    def __init__(self, python_scs, config: PannelConfig, auto_init: bool = True):
        self.python_scs = python_scs
        self.config = config
        if auto_init:
            self.init()

    def __st_dict_card(self, values: dict, col_sizes=[1, 10]):
        '''Desenha um container com borda para exibir informações formatadas'''
        with st.container(border=True):
            for key, value in values.items():
                cols = st.columns(col_sizes)
                cols[0].write(f'**{key}**')
                cols[1].write(str(value))

    @st.dialog('❔ Confirmar ação', width='large')
    def __st_dialog_confirmar_acao(self, acao: str, descricao: str, **kwargs):
        '''Caixa de diálogo para confirmação de ações'''
        st.write(descricao)

        detail_dict = None
        if acao == 'adicionar_script':
            detail_dict = {
                'Destino': f"{self.python_scs.app_path}/{self.python_scs.scripts_folder}/{kwargs['script_nome']}",
                'Prévia': f"```python\n{kwargs['script_bytes'].decode()}```" if kwargs.get('script_bytes', None) else None
            }
        elif acao == 'adicionar_agendamento':
            detail_dict = {
                'Habilitado': '✔ Sim' if kwargs['habilitado'] else '✖ Não',
                'Comentário': kwargs['comentario'] or '_Não preenchido_',
                'Agendamento': f"`{' '.join(kwargs['agendamento'])}`"
            }
            if kwargs.get('comando_customizado', False):
                detail_dict['Comando Customizado'] = f"`{kwargs['comando_customizado']}`"
            else:
                detail_dict['Script'] = f"`{kwargs['script_selecionado']}.py`"

        if detail_dict:
            self.__st_dict_card(detail_dict, col_sizes=[1, 2])

        if acao == 'executar':
            sincrono = st.toggle('Execução síncrona')

        if st.button('Confirmar ação'):
            if acao == 'executar':
                self.python_scs.execute_job(kwargs.get('job'), use_subprocess=not sincrono)
            elif acao == 'toggle':
                self.python_scs.toggle_job(kwargs.get('job'))
            elif acao == 'remover':
                self.python_scs.remove_job(kwargs.get('job'))
            elif acao == 'adicionar_script':
                self.python_scs.upload_script(
                    file_name=kwargs['script_nome'],
                    file_bytes=kwargs['script_bytes']
                )
            elif acao == 'adicionar_agendamento':
                if kwargs['comando_customizado']:
                    self.python_scs.set_job(
                        command=kwargs['comando_customizado'],
                        schedule=kwargs['agendamento'].split(),
                        comment=kwargs['comentario'],
                        enable=kwargs['habilitado']
                    )
                else:
                    self.python_scs.set_script_job(
                        script_name=kwargs['script_selecionado'],
                        schedule=kwargs['agendamento'].split(),
                        comment=kwargs['comentario'],
                        enable=kwargs['habilitado']
                    )
            st.rerun()

    def __st_expander_novo_script(self):
        with st.expander('Enviar novo script', icon='📜'):
            try:
                input_script_arquivo = st.file_uploader('Selecione um arquivo', type=['.py'], accept_multiple_files=False)
                input_script_nome = st.text_input('Nome do arquivo destino', value=input_script_arquivo.name if input_script_arquivo else None)
                script_arquivo = input_script_arquivo.read() if input_script_arquivo else None
                if st.button('Enviar Script'):
                    if not input_script_arquivo:
                        raise ValueError('É necessário selecionar um arquivo')
                    if not input_script_nome:
                        raise ValueError('É necessário informar um nome para o arquivo destino')
                    if not script_arquivo:
                        raise ValueError('O arquivo enviado é inválido')
                    self.__st_dialog_confirmar_acao(
                        'adicionar_script',
                        'Deseja adicionar esse script?',
                        script_nome=input_script_nome,
                        script_bytes=script_arquivo
                    )
            except ValueError as ex:
                st.toast(str(ex), icon='❌')

    def __st_expander_novo_agendamento(self, scripts: List[str]):
        with st.expander('Adicionar novo agendamento', icon='📅'):
            try:
                script_selecionado = st.selectbox('Selecione um script', options=[*scripts, 'Comando customizado'])
                script_selecionado = script_selecionado.split('.')[0]
                comando_customizado = None
                if script_selecionado == 'Comando customizado':
                    comando_customizado = st.text_input('Comando')
                agendamento = st.text_input('Agendamento', value='* * * * *')
                st.markdown('[Verifique como funciona a formatação do agendamento](https://www.site24x7.com/pt/tools/crontab/weekdays-specific-time)')
                comentario = st.text_input('Comentário', value='')
                habilitado = st.toggle('Habilitado', value=True)
                if st.button('Adicionar'):
                    if not agendamento:
                        raise ValueError('É necessário informar um agendamento')
                    if len(agendamento.split(' ')) != 5:
                        raise ValueError('Formato do agendamento inválido: Deve ser composto de 5 partes')
                    if bool(re.search(r"[^0-9/*, -]", agendamento)):
                        raise ValueError('Formato do agendamento inválido: Deve ser composto apenas de / e números')
                    if not comentario:
                        raise ValueError('É necessário informar um comentário')
                    if script_selecionado == 'Comando customizado' and not comando_customizado:
                        raise ValueError('É necessário informar um comando customizado')
                    self.__st_dialog_confirmar_acao(
                        'adicionar_agendamento',
                        'Deseja agendar o script?',
                        script_selecionado=script_selecionado,
                        comando_customizado=comando_customizado,
                        agendamento=agendamento,
                        comentario=comentario,
                        habilitado=habilitado
                    )
            except ValueError as ex:
                st.toast(str(ex), icon='❌')

    def __st_expander_agendamento(
        self,
        job: PythonCronItem,
        allow_execute_job: bool = True,
        allow_toggle_job: bool = True,
        allow_remove_job: bool = True
    ):
        proxima_execucao = job.schedule().get_next().strftime("%d/%m/%Y às %H:%M:%S")
        expander_icon = "✔" if job.enabled else "✖"
        with st.expander(f'**{job.comment or job.script_name}** {" - " + proxima_execucao if job.enabled else ""}', icon=expander_icon, expanded=True):
            st.subheader(job.comment or job.script_name)
            if job.is_running():
                st.success('Este comando está sendo executado')
            col1, col2, col3, space = st.columns([1, 1, 1, 8])
            if allow_execute_job:
                if col1.button('Executar', icon='⚙', key=f'executar_{uuid4()}'):
                    self.__st_dialog_confirmar_acao('executar', 'Deseja executar de forma síncrona esse agendamento?', job=job)
            if allow_toggle_job:
                if col2.button('Habilitar' if not job.enabled else 'Desabilitar', icon='✔' if not job.enabled else '✖', key=f'habilitar_{uuid4()}'):
                    self.__st_dialog_confirmar_acao('toggle', f'Deseja {"habilitar" if not job.enabled else "desabilitar"} esse agendamento?', job=job)
            if allow_remove_job:
                if col3.button('Remover', icon='🗑', key=f'remover_{uuid4()}'):
                    self.__st_dialog_confirmar_acao('remover', 'Deseja remover esse agendamento?', job=job)
            self.__st_dict_card({
                'Script': f'`{job.script_name}.py`',
                'Habilitado': '✔ Sim' if job.enabled else '✖ Não',
                'Comentário': job.comment or '_Não preenchido_',
                'Agendamento': f'`{" ".join(job.schedule().expressions)}`',
                'Arquivo de Logs': f'`{self.python_scs.get_job_log_file_path(job)}.txt`',
                'Próxima execução': proxima_execucao,
                'Comando': f'`{job.command}`'
            })
            st.subheader('Logs')
            logs = self.python_scs.get_job_logs(job)
            st.code(''.join(logs) if logs else 'Nenhum log disponível')

    def init(self):
        '''Gera um painel em Streamlit para gerenciar agendamentos'''
        jobs, scripts = self.python_scs.get_jobs(), self.python_scs.get_scripts()
        st.set_page_config(layout=self.config.layout)

        st.title(self.config.title)
        st.text(self.config.subheader)

        header_1, header_2, header_3 = st.columns(3)
        header_1.metric('Horário Atual', datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S"))
        header_2.metric('Scripts', len(scripts))
        header_3.metric('Agendamentos', len(jobs))

        if self.config.allow_upload_script:
            self.__st_expander_novo_script()

        if self.config.allow_create_job:
            self.__st_expander_novo_agendamento(scripts)

        for job in jobs:
            self.__st_expander_agendamento(
                job,
                allow_execute_job=self.config.allow_execute_job,
                allow_toggle_job=self.config.allow_toggle_job,
                allow_remove_job=self.config.allow_remove_job
            )
