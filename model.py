from tortoise import Model, fields
from wtforms import Form, StringField, IntegerField, Field, widgets
from wtforms.validators import InputRequired
from config import Config
import datetime


class ContainerStatus:
    CREATING = 0
    CREATED = 1
    ERROR = 2
    DELETED = 3


class Container(Model):
    id = fields.IntField(pk=True)
    uid = fields.IntField()
    challenge_id = fields.IntField()
    compose_file = fields.CharField(255)
    status = fields.IntField(default=ContainerStatus.CREATING)
    service_name = fields.CharField(255, null=True)
    node_ip = fields.CharField(100, null=True)
    node_port = fields.IntField(null=True)
    expire = fields.DatetimeField(null=True)

    def __str__(self):
        return f"Container {self.id}: {self.service_name}"

    def to_dict(self):
        return {'status': self.status, 'expire': self.expire.astimezone().isoformat(),
                'node_ip': Config.NODE_MAP.get(self.node_ip, self.node_ip), 'node_port': self.node_port, 'id': self.id}


class ISODateTimeField(Field):
    """
    A text field which stores a `datetime.datetime` matching a format.
    """
    widget = widgets.TextInput()

    def __init__(self, label=None, validators=None, **kwargs):
        kwargs['default'] = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
        super(ISODateTimeField, self).__init__(label, validators, **kwargs)

    def _value(self):
        if self.raw_data:
            return ' '.join(self.raw_data)
        else:
            return self.data and self.data.isoformat() or ''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            try:
                self.data = datetime.datetime.fromisoformat(date_str)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid datetime value'))


class CreateForm(Form):
    uid = IntegerField([InputRequired()])
    challenge = IntegerField([InputRequired()])
    compose_file = StringField([InputRequired()])
    flag = StringField()
    expire = ISODateTimeField()


class RenewForm(Form):
    expire = ISODateTimeField()
