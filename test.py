import asyncio
import asynctest
import datetime
import app as docker_manager
from quart.testing import QuartClient
from tortoise import Tortoise
from model import ContainerStatus
from api.env import recycle_expire_env
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')


class MyTestCase(asynctest.TestCase):
    async def setUp(self):
        # docker_manager.app.run()
        self.app = QuartClient(docker_manager.app)
        await Tortoise.init(db_url="sqlite://:memory:",
                            modules={"models": ["model"]},
                            )
        await Tortoise.generate_schemas(safe=True)
        scheduler = AsyncIOScheduler()
        scheduler.add_job(recycle_expire_env, 'interval', seconds=30)
        scheduler.start()

        # env_initializer()

    async def tearDown(self):
        # In teardown
        logger.info('test finished')
        pass

    async def test_create_delete_1(self):

        logger.info('testing create and delete environment')

        rv = await self.app.post('/env/create',
                                 json={"uid": "1", "challenge": 11, "compose_file": "test/docker-compose.yaml",
                                       "flag": "flag{abc1234}"},
                                 )
        r = await rv.json
        print(await rv.get_data(True))

        self.assertEqual(r['status'], 0)

        for _ in range(50):
            await asyncio.sleep(5)
            t = await self.app.get(f'/env/get/{r["id"]}')
            r = await t.json
            print(await t.get_data(True))
            if r['status'] == ContainerStatus.CREATED:
                break

        self.assertEqual(r['status'], ContainerStatus.CREATED)
        await asyncio.sleep(10)
        t = await self.app.get(f'/env/delete/{r["id"]}')
        r = await t.json
        print(await t.get_data(True))
        self.assertEqual(r['status'], ContainerStatus.DELETED)

    # async def test_create_delete_2(self):
    #
    #     rv = await self.app.post('/env/create',
    #                              json={"uid": "1", "challenge": 11, "compose_file": "docker-compose.yaml",
    #                                    "flag": "flag{111}"},
    #                              )
    #     r = await rv.json
    #     print(r)
    #
    #     self.assertEqual(r['status'], 0)
    #
    #     for _ in range(50):
    #         await asyncio.sleep(5)
    #         t = await self.app.get(f'/env/get/{r["id"]}')
    #         r = await t.json
    #         print(r)
    #         if r['status'] == ContainerStatus.CREATED:
    #             break
    #
    #     self.assertEqual(r['status'], ContainerStatus.CREATED)
    #     await asyncio.sleep(10)
    #     t = await self.app.get(f'/env/delete/{r["id"]}')
    #     r = await t.json
    #     print(r)
    #     self.assertEqual(r['status'], ContainerStatus.DELETED)

    async def test_create_expire(self):

        logger.info('testing create and auto delete expire environment')

        rv = await self.app.post('/env/create',
                                 json={"uid": "1", "challenge": 11,
                                       "compose_file": "test/docker-compose.yaml",
                                       "flag": "flag{test1234}",
                                       "expire": (datetime.datetime.utcnow() + datetime.timedelta(seconds=10)).isoformat()})
        r = await rv.json
        print(await rv.get_data(True))

        self.assertEqual(r['status'], 0)

        for _ in range(50):
            await asyncio.sleep(5)
            t = await self.app.get(f'/env/get/{r["id"]}')
            r = await t.json
            print(await t.get_data(True))
            if r['status'] == ContainerStatus.DELETED:
                break

        self.assertEqual(r['status'], 3)

    async def test_create_renew(self):

        logger.info('testing create and renew environment')

        rv = await self.app.post('/env/create',
                                 json={"uid": "1", "challenge": 11,
                                       "compose_file": "test/docker-compose.yaml",
                                       "flag": "flag{test2020}",
                                       'expire': (datetime.datetime.utcnow() + datetime.timedelta(
                                           seconds=10)).isoformat()})
        r = await rv.json
        print(await rv.get_data(True))

        self.assertEqual(r['status'], 0)

        t = await self.app.post(f'/env/renew/{r["id"]}', json={'expire': (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat()})

        for _ in range(50):
            await asyncio.sleep(5)
            t = await self.app.get(f'/env/get/{r["id"]}')
            r = await t.json
            print(await t.get_data(True))
            if r['status'] == ContainerStatus.CREATED:
                break
        r = await t.json

        self.assertEqual(r['status'], 1)

        logger.info(f'environment started please access http://{r["node_ip"]}:{r["node_port"]}/test.php check if there is flag')

        logger.info('environment will be delete after 60s')
        await asyncio.sleep(60)
        await self.app.get(f'/env/delete/{r["id"]}')


if __name__ == '__main__':
    asynctest.main()
