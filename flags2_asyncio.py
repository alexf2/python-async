import asyncio
import multiprocessing
from collections import Counter
from http import HTTPStatus
from pathlib import Path
from typing import Sequence

import httpx
import tqdm
from httpx import AsyncClient

from flags2_common import DownloadStatus, main, save_flag

DEFAULT_CONCUR_REQ = multiprocessing.cpu_count()
MAX_CONCUR_REQ = 40


print('CPU count: ', DEFAULT_CONCUR_REQ)


async def get_flag(client: AsyncClient, base_url: str, cc: str) -> bytes:
    cc = cc.lower()
    url = f"{base_url}/{cc}/{cc}.gif"

    resp = await client.get(url, timeout=6.1, follow_redirects=True)
    resp.raise_for_status()

    return resp.content


async def download_one(
    client: AsyncClient, cc: str, base_url: str, semaphore: asyncio.Semaphore, verbose: bool
) -> DownloadStatus:
    cc = cc.lower()

    try:
        async with semaphore:
            image = await get_flag(client, base_url, cc)
    except httpx.HTTPStatusError as exc:
        res = exc.response
        if res.status_code == HTTPStatus.NOT_FOUND:
            status = DownloadStatus.NOT_FOUND
            msg = f'not found: {res.url}'
        else:
            raise
    else:
        await asyncio.to_thread(save_flag, image, f"{cc}.gif")
        status = DownloadStatus.OK
        masg = 'OK'

    if verbose and msg:
        print(cc, msg)

    return status


async def supervisor(cc_list: Sequence[str], base_url: str, verbose: bool, concur_req: int) -> Counter[DownloadStatus]:
    counter: Counter[DownloadStatus] = Counter()
    semaphore = asyncio.Semaphore(concur_req)

    async with AsyncClient() as client:
        to_do = (download_one(client, cc, base_url, semaphore, verbose) for cc in sorted(cc_list))
        # res = await asyncio.gather(*to_do)
        to_do_iter = asyncio.as_completed(to_do)
        if not verbose:
            to_do_iter = tqdm.tqdm(to_do_iter, total=len(cc_list))

        error: httpx.HTTPError | None = None
        for coro in to_do_iter:
            try:
                status = await coro
            except httpx.HTTPStatusError as exc:
                error_msg = 'HTTP error {resp.status_code} - {resp.reason_phrase}'
                error_msg = error_msg.format(resp=exc.response)
                error = exc
            except httpx.RequestError as exc:
                error_msg = f'{exc} {type(exc)}'.strip()
                error = exc
            except KeyboardInterrupt:
                break

            if error:
                status = DownloadStatus.ERROR
                if verbose:
                    url = str(error.request.url)
                    cc = Path(url).stem.upper()
                    print(f'{cc} error: {error_msg}')
            counter[status] += 1

    return counter


def download_many(cc_list: Sequence[str], base_url: str, verbose: bool, concur_req: int) -> Counter[DownloadStatus]:
    return asyncio.run(supervisor(cc_list, base_url, verbose, concur_req))


if __name__ == '__main__':
    main(download_many, DEFAULT_CONCUR_REQ, MAX_CONCUR_REQ)
