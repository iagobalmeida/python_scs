from typing import List

import streamlit as st


def st_dict_card(values: dict, col_sizes=[1, 10]):
    """Desenha um container com borda para exibir informações formatadas"""
    with st.container(border=True):
        for key, value in values.items():
            cols = st.columns(col_sizes)
            cols[0].write(f'**{key}**')
            cols[1].write(str(value))


@st.dialog('❔ Confirmar ação', width='large')
def st_dialog_confirmar_acao(python_scs, acao: str, descricao: str, **kwargs):
    """Caixa de diálogo para confirmação de ações"""
    st.write(descricao)
    detail_dict = None
    if acao == 'adicionar_script':
        detail_dict = {
            'Destino': f"{python_scs.app_path}/{python_scs.scripts_folder}/{kwargs['script_nome']}",
            'Prévia': f"```python\n{kwargs['script_bytes'].decode()}```" if kwargs.get('script_bytes') else None
        }
    elif acao == 'adicionar_agendamento':
        detail_dict = {
            'Habilitado': '✔ Sim' if kwargs['habilitado'] else '✖ Não',
            'Comentário': kwargs['comentario'] or '_Não preenchido_',
            'Agendamento': f"`{' '.join(kwargs['agendamento'])}`"
        }
        if kwargs.get('comando_customizado'):
            detail_dict['Comando Customizado'] = f"`{kwargs['comando_customizado']}`"
        else:
            detail_dict['Script'] = f"`{kwargs['script_selecionado']}.py`"

    if detail_dict:
        st_dict_card(detail_dict, col_sizes=[1, 2])

    sincrono = st.toggle('Execução síncrona') if acao == 'executar' else None

    if st.button('Confirmar ação'):
        if acao == 'executar':
            python_scs.execute_job(kwargs.get('job'), use_subprocess=not sincrono)
        elif acao == 'toggle':
            python_scs.toggle_job(kwargs.get('job'))
        elif acao == 'remover':
            python_scs.remove_job(kwargs.get('job'))
        elif acao == 'adicionar_script':
            python_scs.upload_script(
                file_name=kwargs['script_nome'],
                file_bytes=kwargs['script_bytes']
            )
        elif acao == 'adicionar_agendamento':
            if kwargs['comando_customizado']:
                python_scs.set_job(
                    command=kwargs['comando_customizado'],
                    schedule=kwargs['agendamento'].split(),
                    comment=kwargs['comentario'],
                    enable=kwargs['habilitado']
                )
            else:
                python_scs.set_script_job(
                    script_name=kwargs['script_selecionado'],
                    schedule=kwargs['agendamento'].split(),
                    comment=kwargs['comentario'],
                    enable=kwargs['habilitado']
                )
        st.rerun()


def st_expander_novo_script(python_scs):
    with st.expander('Enviar novo script', icon='📜'):
        input_script_arquivo = st.file_uploader('Selecione um arquivo', type=['.py'])
        input_script_nome = st.text_input('Nome do arquivo destino', value=input_script_arquivo.name if input_script_arquivo else '')
        if st.button('Enviar Script'):
            if not input_script_arquivo:
                st.toast('É necessário selecionar um arquivo', icon='❌')
                return
            st_dialog_confirmar_acao(
                python_scs, 'adicionar_script', 'Deseja adicionar esse script?',
                script_nome=input_script_nome,
                script_bytes=input_script_arquivo.read()
            )


def st_expander_novo_agendamento(python_scs, scripts: List[str]):
    with st.expander('Adicionar novo agendamento', icon='📅'):
        script_selecionado = st.selectbox('Selecione um script', options=[*scripts, 'Comando customizado'])
        comando_customizado = st.text_input('Comando') if script_selecionado == 'Comando customizado' else None
        agendamento = st.text_input('Agendamento', value='* * * * *')
        comentario = st.text_input('Comentário', value='')
        habilitado = st.toggle('Habilitado', value=True)
        if st.button('Adicionar'):
            st_dialog_confirmar_acao(
                python_scs, 'adicionar_agendamento', 'Deseja agendar o script?',
                script_selecionado=script_selecionado,
                comando_customizado=comando_customizado,
                agendamento=agendamento,
                comentario=comentario,
                habilitado=habilitado
            )


def st_expander_agendamento(python_scs, job, allow_execute_job: bool = True, allow_toggle_job: bool = True, allow_remove_job: bool = True):
    description = job.comment or job.script_name
    proxima_execucao = job.schedule().get_next().strftime("%d/%m/%Y às %H:%M:%S")
    expander_icon = "✔" if job.enabled else "✖"
    with st.expander(f'**{description}** {" - " + proxima_execucao if job.enabled else ""}', icon=expander_icon, expanded=True):
        st.subheader(description)
        if job.is_running():
            st.success('Este comando está sendo executado')
        col1, col2, col3, space = st.columns([1, 1, 1, 8])
        if allow_execute_job:
            if col1.button('Executar', icon='⚙', key=f'executar_{description}'):
                st_dialog_confirmar_acao(python_scs, 'executar', 'Deseja executar de forma síncrona esse agendamento?', job=job)
        if allow_toggle_job:
            if col2.button('Habilitar' if not job.enabled else 'Desabilitar', icon='✔' if not job.enabled else '✖', key=f'habilitar_{description}'):
                st_dialog_confirmar_acao(python_scs, 'toggle', f'Deseja {"habilitar" if not job.enabled else "desabilitar"} esse agendamento?', job=job)
        if allow_remove_job:
            if col3.button('Remover', icon='🗑', key=f'remover_{description}'):
                st_dialog_confirmar_acao(python_scs, 'remover', 'Deseja remover esse agendamento?', job=job)
        st_dict_card({
            'Script': f'`{job.script_name}.py`',
            'Habilitado': '✔ Sim' if job.enabled else '✖ Não',
            'Comentário': job.comment or '_Não preenchido_',
            'Agendamento': f'`{" ".join(job.schedule().expressions)}`',
            'Arquivo de Logs': f'`{python_scs.get_job_log_file_path(job)}.txt`',
            'Próxima execução': proxima_execucao,
            'Comando': f'`{job.command}`'
        })
        st.subheader('Logs')
        logs = python_scs.get_job_logs(job)
        st.code(''.join(logs) if logs else 'Nenhum log disponível')


def init(
    python_scs,
    layout='wide',
    title='Scripts Manager',
    subheader='Manage your python scripts',
    allow_execute_job=True,
    allow_toggle_job=True,
    allow_remove_job=True,
    allow_upload_script=True,
    allow_create_job=True
):
    """Gera um painel em Streamlit para gerenciar agendamentos"""
    jobs, scripts = python_scs.get_jobs(), python_scs.get_scripts()
    st.set_page_config(layout=layout)

    st.title(title)
    st.text(subheader)

    if allow_upload_script:
        st_expander_novo_script(python_scs)
    if allow_create_job:
        st_expander_novo_agendamento(python_scs, scripts)
    for job in jobs:
        st_expander_agendamento(python_scs, job, allow_execute_job, allow_toggle_job, allow_remove_job)
