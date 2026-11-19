import argparse
import time
from collections import Counter
from enum import Enum
from pathlib import Path
from typing import Sequence

DownloadStatus = Enum("DownloadStatus", "OK NOT_FOUND ERROR")

POP20_CC = (
    'CN',
    'IN',
    'US',
    'ID',
    'BR',
    'PK',
    'NG',
    'BD',
    'RU',
    'JP',
    'MX',
    'PH',
    'VN',
    'ET',
    'EG',
    'DE',
    'IR',
    'TR',
    'CD',
    'FR',
)

SERVERS = {
    "REMOTE": "https://www.fluentpython.com/data/flags",
    "LOCAL": "http://localhost:8000/flags",
    "DELAY": "http://localhost:8001/flags",
    "ERROR": "http://localhost:8002/flags",
}

DEFAULT_SERVER = 'REMOTE'

DEST_DIR = Path("downloaded")


def save_flag(img: bytes, filename: str) -> None:
    (DEST_DIR / filename).write_bytes(img)


def initial_report(cc_list: Sequence[str], actual_req: int, server_label: str) -> None:
    if len(cc_list) <= 10:
        cc_msg = ", ".join(cc_list)
    else:
        cc_msg = f"from {cc_list[0]} to {cc_list[-1]}"

    print(f"{server_label} site: {SERVERS[server_label]}")
    plural = "s" if len(cc_list) != 1 else ""
    print(f"Searching for {len(cc_list)} flag{plural}: {cc_msg}")

    if actual_req == 1:
        print("1 connection will be used.")
    else:
        print(f"{actual_req} concurrent connections will be used.")


def final_report(cc_list: Sequence[str], counter: Counter[DownloadStatus], start_time: float) -> None:
    elapsed = time.perf_counter() - start_time
    print("-" * 20)
    plural = "s" if counter[DownloadStatus.OK] != 1 else ""

    print(f"{counter[DownloadStatus.OK]:3} flag{plural} downloaded.")
    if counter[DownloadStatus.NOT_FOUND]:
        print(f"{counter[DownloadStatus.NOT_FOUND]:3} not found.")
    if counter[DownloadStatus.ERROR]:
        plural = "s" if counter[DownloadStatus.ERROR] != 1 else ""
        print(f"{counter[DownloadStatus.ERROR]:3} error{plural}.")

    print(f"Elapsed time: {elapsed:.2f}s")


def process_args(default_concur_req):
    parser = argparse.ArgumentParser(
        description="Download flags for country codes. " "Default: top 20 countries by population."
    )

    parser.add_argument(
        '-m',
        '--max_req',
        metavar='CONCURRENT',
        type=int,
        default=default_concur_req,
        help=f'maximum concurrent requests (default={default_concur_req})',
    )

    server_options = ', '.join(sorted(SERVERS))
    parser.add_argument(
        '-s',
        '--server',
        metavar='LABEL',
        default=DEFAULT_SERVER,
        help=f'Server to hit; one of {server_options} ' f'(default={DEFAULT_SERVER})',
    )

    parser.add_argument('-v', '--verbose', action='store_true', help='output detailed progress info')

    return parser.parse_args(), sorted(POP20_CC)


def main(download_many, default_concur_req, max_concur_req):
    args, cc_list = process_args(default_concur_req)
    actual_req = min(args.max_req, max_concur_req, len(cc_list))

    initial_report(cc_list, actual_req, args.server)

    base_url = SERVERS[args.server]
    DEST_DIR.mkdir(exist_ok=True)

    t0 = time.perf_counter()
    counter = download_many(cc_list, base_url, args.verbose, actual_req)
    final_report(cc_list, counter, t0)
