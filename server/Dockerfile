FROM alpine
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk add --update docker-cli python3 py3-pip \
                     gcc python3-dev musl-dev

RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ quart Hypercorn \
                    tortoise-orm pyyaml wtforms wtforms_json asynctest docker-py APScheduler \
                    asyncpg

WORKDIR /docker-manager
ENTRYPOINT 'sh'

# sudo docker run --rm -it -v /home/li/docker/docker-manager:/opt/project -v /var/run/docker.sock:/var/run/docker.sock -v /data/nfs:/data/flag/ -v /home/li/docker/docker-manager/data/compose:/data/compose c1ctf-docker-manager