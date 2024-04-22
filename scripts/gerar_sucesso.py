from datetime import datetime
from logging import getLogger

log = getLogger('gerar_sucesso')


def main():
    log.warning('Isso e um aviso')
    return True


if __name__ == '__main__':
    log.warning(f'\n[{datetime.now()}] - Executing "{log.name}"...')
    main()
