# Python CronTab Manager

Módulo para gestão de scripts python executados com cron a partir de registros de um banco de dados.

## Dependências
```
python-crontab==3.0.0
pytest
croniter
cron_descriptor
```

## Introdução

Esse projeto possuí um arquivo chamado `python_crontab.py`, referente ao módulo para gestão do `cron` em si.

Existe também um arquivo chamado `db.py` que é uma abstração de um banco de dados qualquer, que possuí uma tabela chamada `crontabs` com 3 colunas:
- *marker* `str`: Um marcador para agregar scripts com um mesmo escopo.
- *comment* `str`: O nome do arquivo contido em `src/scripts/` que será executado.
- *schedule* `str`: A configuração de agendamento do cron, seguindo o padrão `* * * * *`.

Em `src/tests/test.py` existe um teste que busca os dados da abstração de banco e atualiza o arquivo de configuração do cron da máquina (Antes de configurar os scripts cadastrados no banco, o arquivo de configuração do Cron é limpo).

É importante estudar o método `src/modules/db.py::DBInterface.get_crontabs()` pois nele existe uma função interna responsável por transformar os registros do banco de dados em uma entidade `CronJob` que é utilizada para garantir uma boa comunicação com o módulo.

Esse método consome o método de classe `PythonCrontrabInterface.cron_job()` para gerar uma entidade `CronJob`, use esse método na sua aplicação para gerar uma entidade válida para as funções `get_jobs`, `set_job` e `set_jobs`.
