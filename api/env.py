from quart import Blueprint, request, jsonify
from model import Container, ContainerStatus, CreateForm, RenewForm
from util.common import write_flag, read_compose, update_compose_flag, docker_deploy
from util.service import update_status, delete_environment
import datetime
import asyncio

env = Blueprint('env', __name__, url_prefix='/env')


async def recycle_expire_env():
    c = await Container.filter(status__in=[ContainerStatus.CREATED, ContainerStatus.CREATING])
    now = datetime.datetime.utcnow()
    for container in c:
        if container.status == ContainerStatus.CREATING:
            await update_status(container)
        if container.status == ContainerStatus.CREATED and container.expire and container.expire < now:
            await delete_environment(container)


@env.route('/create', methods=['POST'])
async def create():
    form = CreateForm.from_json(await request.json)

    compose_data = read_compose(form.compose_file.data)
    if None != form.flag.data:
        flag_volume = f"{form.uid.data}-{form.challenge.data}"
        write_flag(flag_volume, form.flag.data)
        compose_data = update_compose_flag(compose_data, flag_volume)

    container_num = len(compose_data['services'])
    container = await Container.create(uid=form.uid.data, challenge_id=form.challenge.data,
                                       compose_file=form.compose_file.data, status=ContainerStatus.CREATING,
                                       expire=form.expire.data)

    async def deploy():
        services = await docker_deploy(compose_data, form.uid.data)
        container.service_name = '|'.join(services)

        if container_num != len(services):
            container.status = ContainerStatus.ERROR

        await container.save(update_fields=['service_name', 'status'])
        # 不在这里更新，以免因为其他地方修改了过期时间等参数
        # await update_status(container)

    loop = asyncio.get_event_loop()
    loop.create_task(deploy())

    return jsonify({'status': ContainerStatus.CREATING, 'id': container.id})


@env.route('/list', methods=['GET'])
async def getlist():
    data = await Container.all()
    r = [c.to_dict() for c in data]
    return jsonify(r)


@env.route('/get/<int:env_id>', methods=['GET'])
async def get(env_id):
    container = await Container.get(id=env_id)
    if container.service_name is not None and len(container.service_name) > 0:
        await update_status(container)
    return jsonify(container.to_dict())


@env.route('/renew/<int:env_id>', methods=['POST'])
async def renew(env_id):
    form = RenewForm.from_json(await request.json)
    c = await Container.get(id=env_id)
    if c.status == ContainerStatus.ERROR or c.status == ContainerStatus.DELETED:
        return jsonify({'status': -1})
    c.expire = form.expire.data
    await c.save(update_fields=['expire'])
    return jsonify({'status': c.status, 'expire': c.expire.astimezone().isoformat()})


@env.route('/delete/<int:env_id>', methods=['GET'])
async def delete(env_id):
    c = await Container.get(id=env_id)
    if c.status != ContainerStatus.CREATED:
        return jsonify({'status': -1})
    await delete_environment(c)
    return jsonify({'status': c.status})
