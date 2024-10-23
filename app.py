from quart import Quart
from api.env import env, recycle_expire_env
from tortoise.contrib.quart import register_tortoise
from config import Config
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import wtforms_json
import logging

logging.getLogger('db_client').setLevel(logging.DEBUG)
logging.getLogger('util.common').setLevel(logging.DEBUG)
logging.getLogger('util.service').setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)

app = Quart(__name__)

app.register_blueprint(env)

register_tortoise(
    app,
    db_url=Config.DB_URL,
    modules={"models": ["model"]},
    generate_schemas=True,
)

wtforms_json.init()


@app.before_serving
async def register_recycle():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(recycle_expire_env, 'interval', seconds=30)
    scheduler.start()


#
# @app.route('/')
# def hello_world():
#     return 'Hello World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
