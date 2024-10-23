import os
import yaml
from config import Config
from asyncio.subprocess import PIPE, create_subprocess_exec
import re
import logging

logger = logging.getLogger(__name__)


def write_flag(name, flag) -> None:
    user_flag_dir = os.path.join(Config.FLAG_DIR, name)
    try:
        os.makedirs(user_flag_dir)
    except Exception as e:
        pass
    with open(os.path.join(user_flag_dir, "flag"), 'w') as f:
        f.write(flag)


def read_compose(name) -> dict:
    with open(os.path.join(Config.COMPOSE_DIR, name), 'r') as f:
        return yaml.safe_load(f.read())


def update_compose_flag(compose_data: dict, flag_volume) -> dict:
    # t = compose_data)
    volumes = compose_data.get('volumes', {})
    for key in volumes.keys():
        if 'flag' in key:
            volumes[key] = {'driver_opts': {'type': 'nfs4', 'o': f'addr={Config.DISK_IP},nolock,soft,ro',
                                            'device': f':/{flag_volume}'}}
    compose_data['volumes'] = volumes
    return compose_data


async def docker_deploy(compose: dict, uid):
    data = yaml.dump(compose).encode('utf-8')
    logger.debug('deploying service')
    p = await create_subprocess_exec('/usr/bin/docker', 'stack', 'deploy', '-c', '-', f'user{uid}',
                                     stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = await p.communicate(data)
    logger.debug("stdout:" + out.decode('utf-8'))
    logger.debug("stderr:" + err.decode('utf-8'))
    if b'Error' in err:
        return []
    services = re.findall(r'service (\w+)', out.decode('utf-8'), re.M)
    return services
