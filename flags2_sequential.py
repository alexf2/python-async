from collections import Counter
from http import HTTPStatus
from urllib.parse import urljoin

import httpx
import tqdm  # type: ignore

from flags2_common import DownloadStatus, main, save_flag


def get_flag(base_url: str, cc: str) -> bytes:
    cc = cc.lower()
    url = urljoin(base_url + "/", f"{cc}/{cc}.gif")

    resp = httpx.get(url, timeout=3.1, follow_redirects=True)
    resp.raise_for_status()

    return resp.content


def download_one(cc: str, base_url: str, verbose: bool = False) -> DownloadStatus:
    try:
        image = get_flag(base_url, cc)
    except httpx.HTTPStatusError as exc:
        res = exc.response
        if res.status_code == HTTPStatus.NOT_FOUND:
            status = DownloadStatus.NOT_FOUND
            msg = f'not found: {res.url}'
        else:
            raise
    else:
        save_flag(image, f'{cc}.gif')
        status = DownloadStatus.OK
        msg = 'OK'

    if verbose:
        print(cc, msg)

    return status


def download_many(cc_list: list[str], base_url: str, verbose: bool, _unused_concur_req: int) -> Counter[DownloadStatus]:
    counter: Counter[DownloadStatus] = Counter()
    cc_iter = sorted(cc_list)

    if not verbose:
        cc_iter = tqdm.tqdm(cc_iter)

    for cc in cc_iter:
        try:
            status = download_one(cc, base_url, verbose)
        except httpx.HTTPStatusError as exc:
            error_msg = 'HTTP error {resp.status_code} - {resp.reason_phrase}'
            error_msg = error_msg.format(resp=exc.response)
        except httpx.RequestError as exc:
            error_msg = f'{exc} {type(exc)}'.strip()
        except KeyboardInterrupt:
            break
        else:
            error_msg = ''

        if error_msg:
            status = DownloadStatus.ERROR
        counter[status] += 1

        if verbose and error_msg:
            print(f'{cc} error: {error_msg}')

    return counter


if __name__ == '__main__':
    main(download_many, 1, 1)
