from datetime import datetime
from logging import getLogger

log = getLogger('gerar_erro')


def main():
    print(1/0)


if __name__ == '__main__':
    log.warning(f'\n[{datetime.now()}] - Executing "{log.name}"...')
    main()
