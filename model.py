import traceback

from framework import db
from framework.util import Util
from mod import P

name = 'wol'
logger = P.logger
package_name = P.package_name


class ModelWOL(db.Model):
    __tablename__ = f'{name}_wol'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    mac = db.Column(db.String, nullable=False)
    ip = db.Column(db.String, nullable=False)

    def __init__(self, wol_name: str, mac: str, ip: str):
        self.name = wol_name
        self.mac = mac
        self.ip = ip

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self) -> dict:
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

    @staticmethod
    def to_dict() -> list:
        try:
            ret = Util.db_to_dict(db.session.query(ModelWOL).all())
            return ret
        except Exception as exception:
            logger.error('Exception:%s', exception)
            logger.error(traceback.format_exc())
            return []

    @staticmethod
    def find(db_id: int):
        try:
            return db.session.query(ModelWOL).filter_by(id=db_id).first()
        except Exception as e:
            logger.error('Exception:%s %s', e, db_id)
            logger.error(traceback.format_exc())

    @staticmethod
    def create(wol_name: str, mac: str, ip: str):
        try:
            entity = ModelWOL(wol_name, mac, ip)
            db.session.add(entity)
            db.session.commit()
            return entity
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return None

    def update(self, wol_name: str, mac: str, ip: str) -> bool:
        try:
            self.name = wol_name
            self.mac = mac
            self.ip = ip
            db.session.commit()
            return True
        except Exception as e:
            logger.error('Exception:%s %s', e, self.id)
            logger.error(traceback.format_exc())
            return False

    def delete(self) -> bool:
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            logger.error('Exception:%s %s', e, self.id)
            logger.error(traceback.format_exc())
            return False
