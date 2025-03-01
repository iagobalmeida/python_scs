import asyncio
from datetime import datetime
from logging import getLogger

log = getLogger('gerar_sucesso')


async def main():
    for _ in range(30):
        log.warning(f'\n[{datetime.now()}] - OK')
        await asyncio.sleep(.5)
    return True


if __name__ == '__main__':
    log.warning(f'\n[{datetime.now()}] - Executing "{log.name}"...')
    asyncio.run(main())
