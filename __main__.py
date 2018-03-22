# coding=utf8
import typing
import requests
import io
import yaml
import dataclasses
import delegator
import pathlib
import os
import elib
import youtube_dl

YAML_LIST_URL = r'https://rawgit.com/132nd-etcher/7c70127508cf88ccc355bfbf67e2ea3d/raw/yt.yml'
LOGGER = elib.custom_logging.get_logger('PITUBE', log_to_file=True, use_click_handler=False, console_level='DEBUG')


def build_command(name: str, url: str, stream_config: dict):
    LOGGER.info(f'Downloading: {name}')
    with youtube_dl.YoutubeDL(stream_config) as ytdl:
        ytdl.download([url])


def get_config_from_env(options: dict):
    values = ['PITUBE_FORMAT', 'PITUBE_OUTTMPL', 'PITUBE_DOWNLOAD_ARCHIVE']
    for val in values:
        val_from_env = os.getenv(val)
        if val_from_env:
            LOGGER.warning(f'value overwritten in ENV: {val}')
            attr_name = val.replace('PITUBE_', '').lower()
            options[attr_name] = val_from_env


def load_config() -> typing.Tuple[dict, dict]:
    LOGGER.info('loading config')
    if pathlib.Path('test.yml').exists():
        LOGGER.warning('using local "test.yml" file')
        content = pathlib.Path('test.yml').read_bytes()
    else:
        LOGGER.debug('loading Gist config')
        req = requests.get(YAML_LIST_URL)
        if not req.ok:
            LOGGER.error(f'request failed: {req.reason}')
            exit(-1)
        content = req.content
    LOGGER.debug('decoding config')
    # noinspection PyTypeChecker
    req_text = io.TextIOWrapper(io.BytesIO(content), encoding='utf8')
    print(req_text.read())
    req_text.seek(0)
    LOGGER.debug('parsing config YAML into dictionary')
    yaml_config = yaml.load(req_text)
    options = yaml_config['options']
    LOGGER.debug('loading config from ENV variables')
    get_config_from_env(options)
    LOGGER.info('config loaded')
    return yaml_config['options'], yaml_config['streams']


def main():
    options, streams = load_config()
    print(options)
    for stream in streams:
        stream_config = dict(options)
        if 'options' in stream:
            stream_config.update(stream['options'])
        build_command(stream['name'], stream['url'], stream_config)


if __name__ == "__main__":
    main()
