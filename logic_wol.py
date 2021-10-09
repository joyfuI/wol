import traceback
import json
import re
import socket
from struct import pack

from flask import render_template, jsonify

from plugin import LogicModuleBase
from mod import P
from system.model import ModelSetting as SystemModelSetting

from .model import ModelWOL

name = 'wol'
logger = P.logger
ModelSetting = P.ModelSetting
package_name = P.package_name


class LogicWOL(LogicModuleBase):
    db_default = {
        f'{name}_db_version': '1',
        f'{name}_port': 7
    }

    def __init__(self, p):
        super(LogicWOL, self).__init__(p, 'wol')
        self.name = name

    def process_menu(self, sub, req):
        try:
            arg = {
                'package_name': package_name,
                'sub': name,
                'sub2': sub
            }

            if sub == 'setting':
                arg.update(ModelSetting.to_dict())

            elif sub == 'wol':
                arg['ddns'] = SystemModelSetting.get('ddns')
                arg['api'] = f'apikey={SystemModelSetting.get("auth_apikey")}&' if SystemModelSetting.get_bool(
                    'auth_use_apikey') else ''
                arg['list'] = json.dumps(ModelWOL.to_dict())

            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f'{package_name} - {sub}')

    def process_ajax(self, sub, req):
        try:
            logger.debug('AJAX: %s, %s', sub, req.values)
            ret = {'ret': 'success'}

            if sub == 'create':
                wol_name = req.form['name'].strip()
                mac = req.form['mac'].strip()
                ip = req.form['ip'].strip()
                p = re.compile('^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$')
                if not wol_name or not mac or p.match(mac) is None or not ip:
                    ret['ret'] = 'warning'
                    ret['msg'] = '잘못된 요청'
                else:
                    ModelWOL.create(wol_name, mac, ip)

            if sub == 'read':
                ret['data'] = ModelWOL.to_dict()

            if sub == 'delete':
                wol_id = req.form['id']
                if not wol_id:
                    ret['ret'] = 'warning'
                    ret['msg'] = '잘못된 요청'
                else:
                    wol = ModelWOL.find(wol_id)
                    wol.delete()

            if sub == 'wake':
                wol_id = req.form['id']
                if not wol_id:
                    ret['ret'] = 'warning'
                    ret['msg'] = '잘못된 요청'
                else:
                    wol = ModelWOL.find(wol_id)
                    LogicWOL.send_wol(wol.mac, wol.ip)
                    ret['msg'] = '매직 패킷 전송 성공'

            return jsonify(ret)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return jsonify({'ret': 'danger', 'msg': str(e)})

    def process_api(self, sub, req):
        try:
            logger.debug('API: %s, %s', sub, req.values)
            ret = {'ret': 'success'}

            if sub == 'wake':
                wol_id = req.values.get('id')
                if not wol_id:
                    ret['ret'] = 'warning'
                    ret['msg'] = '잘못된 요청'
                else:
                    wol = ModelWOL.find(wol_id)
                    if wol is None:
                        ret['ret'] = 'danger'
                        ret['msg'] = '존재하지 않는 id'
                    else:
                        LogicWOL.send_wol(wol.mac, wol.ip)
                        ret['msg'] = '매직 패킷 전송 성공'

            return jsonify(ret)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return jsonify({'ret': 'danger', 'msg': str(e)})

    # 매직패킷 전송
    @staticmethod
    def send_wol(mac: str, ip: str) -> None:
        sep = mac[2]
        mac = mac.replace(sep, '')  # 구분자 제거
        port = ModelSetting.get_int(f'{name}_port')

        data = b'FFFFFFFFFFFF' + (mac * 16).encode()
        send_data = b''

        for i in range(0, len(data), 2):
            send_data += pack('B', int(data[i:i + 2], 16))

        logger.debug('wake: %s, %s', mac, ip)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(send_data, (ip, port))
