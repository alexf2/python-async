import asyncio
import socket
from keyword import kwlist

MAX_KEYWORD = 4


async def probe(domain: str) -> tuple[str, bool]:
    loop = asyncio.get_running_loop()
    try:
        await loop.getaddrinfo(domain, None)
    except socket.gaierror:
        return (domain, False)

    return (domain, True)


async def main() -> None:
    names = filter(lambda d: len(d) <= MAX_KEYWORD, kwlist)
    domains = (f'{name}.dev'.lower() for name in names)

    coros = map(lambda d: probe(d), domains)
    # тут мы получаем coroutines по мере завершения
    # as_completed не ждёт всех, а порядок не будет совпадать с порядком запросов
    for coro in asyncio.as_completed(coros):
        # тут корутина coro уже завершена, но await нужен, чтобы получить результат либо исключение
        domain_name, found = await coro
        mark = '+' if found else ' '
        print(f'{mark} {domain_name}')


if __name__ == '__main__':
    asyncio.run(main())
