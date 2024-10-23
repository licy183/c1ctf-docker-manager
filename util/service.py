import docker
from model import ContainerStatus
import logging

logger = logging.getLogger(__name__)


async def update_status(container) -> None:
    logger.debug(f"update {container.id}")

    # 创建service_name为空表明还没创建成功
    if container.status != ContainerStatus.CREATING or container.service_name is None:
        return
    services = container.service_name.split('|')
    container_num = len(services)

    client = docker.from_env()

    all_service_finished = True
    # 假定只有一个输出的port
    for i in range(container_num):
        tasks = client.tasks(filters={"service": services[i]})
        svc = client.inspect_service(services[i])
        if svc is None:
            container.status = ContainerStatus.ERROR
            break
        # ingress类型的port在svc中
        for port in svc['Endpoint'].get('Ports', ()):
            if port.get('PublishedPort'):
                container.node_port = int(port.get('PublishedPort'))

        # host类型的port在task中
        for task in tasks:
            if task['DesiredState'] != 'running':
                continue
            for port_status in task['Status'].get('PortStatus'):
                for port in port_status.get('Ports'):
                    if port.get('PublishedPort'):
                        container.node_port = int(port.get('PublishedPort'))

            # 如果在这个service中发现公开了的端口
            if container.node_port != 0 and container.node_ip is None:
                # node_list = client.nodes()
                node_id = task.get('NodeID')
                container.node_ip = node_id

            if task['Status']['State'] != 'running':
                all_service_finished = False
    client.close()
    if all_service_finished:
        container.status = ContainerStatus.CREATED
    await container.save()


async def delete_environment(container) -> None:
    logger.debug(f"delete {container.id}")
    if container.status != ContainerStatus.CREATED:
        return
    client = docker.from_env()
    services = container.service_name.split('|')
    for service in services:
        client.remove_service(service)
    container.status = ContainerStatus.DELETED
    client.close()
    await container.save()
