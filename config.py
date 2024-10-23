class Config:
    FLAG_DIR = '/data/flag/'
    COMPOSE_DIR = '/data/compose/'
    DISK_IP = '192.168.193.129'
    # DB_URL = 'sqlite://:memory:'
    DB_URL = 'postgres://c1ctf:c1ctf@c1ctf-docker-manager-db:5432/c1ctf'
    NODE_MAP = {
        'xxxxx': '192.168.193.129'
    }
