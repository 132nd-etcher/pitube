import requests
import io
import yaml
import dataclasses
import delegator
import pathlib
import os
import elib


YAML_LIST_URL = r'https://gist.github.com/132nd-etcher/7c70127508cf88ccc355bfbf67e2ea3d/raw/fa381c9957e1eb5cab6b2c5cbb6cc013cc8b1731/yt.yml'
LOGGER = elib.custom_logging.get_logger('PITUBE', log_to_file=True, use_click_handler=False, console_level='DEBUG')


@dataclasses.dataclass
class GlobalConfig:
    format: str
    destination: str
    archive: str
    quality: int
    playlist_end: int
    streams: list
    base_cmd: str = 'youtube-dl'


@dataclasses.dataclass
class StreamConfig:
    name: str
    url: str
    format: str = None
    destination: str = None
    archive: str = None
    quality: int = None
    playlist_end: int = None


def build_command(global_config: GlobalConfig, stream_config: StreamConfig):
    LOGGER.info(f'Downloading: {stream_config.name}')
    format = stream_config.format or global_config.format
    destination = stream_config.destination or global_config.destination
    output = f'{str(pathlib.Path(destination).absolute())}/{format}'
    archive = stream_config.archive or global_config.archive
    archive = str(pathlib.Path(archive).absolute())
    quality = stream_config.quality or global_config.quality
    playlist_end = stream_config.playlist_end or global_config.playlist_end
    cmd = io.StringIO()
    cmd.write(global_config.base_cmd)
    cmd.write(f' -o "{output}"')
    cmd.write(f' --download-archive "{archive}"')
    cmd.write(f' -f {quality}')
    cmd.write(f' --playlist-end {playlist_end}')
    cmd.write(f' "{stream_config.url}"')
    cmd.seek(0)
    cmd = cmd.read()
    print(cmd)


def get_config_from_env(config: GlobalConfig) -> GlobalConfig:
    values = ['PITUBE_FORMAT', 'PITUBE_DESTINATION', 'PITUBE_ARCHIVE', 'PITUBE_QUALITY']
    for val in values:
        val_from_env = os.getenv(val)
        if val_from_env:
            LOGGER.warning(f'value overwritten in ENV: {val}')
            attr_name = val.replace('PITUBE_', '').lower()
            setattr(config, attr_name, val_from_env)
    return config


def load_config() -> GlobalConfig:
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
    LOGGER.debug('parsing config YAML into dictionary')
    config = yaml.load(req_text)
    config = GlobalConfig(**config)
    LOGGER.debug('loading config from ENV variables')
    get_config_from_env(config)
    LOGGER.info('config loaded')
    return config

def main():
    global_config = load_config()
    print(global_config)
    for stream in global_config.streams:
        # print(stream)
        stream_config = StreamConfig(**stream)
        build_command(global_config, stream_config)


if __name__ == "__main__":
    main()
