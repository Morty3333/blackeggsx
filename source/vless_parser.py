"""
Модуль для парсинга VLESS URL
"""
import urllib.parse
import base64
from typing import Dict, Optional


class VLESSURLParser:
    """Парсер для VLESS URL формата: vless://uuid@host:port?params#remark"""
    
    @staticmethod
    def parse(vless_url: str) -> Dict[str, any]:
        """
        Парсит VLESS URL и возвращает словарь с параметрами
        
        Формат: vless://uuid@host:port?params#remark
        """
        if not vless_url.startswith('vless://'):
            raise ValueError("URL должен начинаться с 'vless://'")
        
        # Удаляем префикс
        url_without_protocol = vless_url[8:]
        
        # Разделяем на части: uuid@host:port?params#remark
        parts = url_without_protocol.split('#', 1)
        remark = parts[1] if len(parts) > 1 else None
        
        url_part = parts[0]
        query_part = ''
        
        # Разделяем на URL и query параметры
        if '?' in url_part:
            url_part, query_part = url_part.split('?', 1)
        
        # Парсим uuid@host:port
        if '@' not in url_part:
            raise ValueError("Неверный формат URL: отсутствует UUID")
        
        uuid, address = url_part.split('@', 1)
        
        # Парсим host:port
        if ':' not in address:
            raise ValueError("Неверный формат URL: отсутствует порт")
        
        host, port = address.rsplit(':', 1)
        port = int(port)
        
        # Парсим query параметры
        params = {}
        if query_part:
            for param in query_part.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = urllib.parse.unquote(value)
        
        result = {
            'uuid': uuid,
            'host': host,
            'port': port,
            'remark': remark,
            'params': params
        }
        
        # Извлекаем стандартные параметры
        result['type'] = params.get('type', 'tcp')
        result['security'] = params.get('security', 'none')
        result['encryption'] = params.get('encryption', 'none')
        result['flow'] = params.get('flow', '')
        
        # Парсим специальные параметры в зависимости от типа
        if result['type'] == 'ws':
            result['path'] = params.get('path', '/')
            result['host_header'] = params.get('host', host)
        elif result['type'] == 'grpc':
            result['serviceName'] = params.get('serviceName', '')
        elif result['type'] == 'tcp':
            result['headerType'] = params.get('headerType', 'none')
        
        # SNI для TLS
        if 'sni' in params:
            result['sni'] = params['sni']
        elif 'host' in params and result['type'] != 'ws':
            result['sni'] = params['host']
        
        # ALPN для TLS
        if 'alpn' in params:
            result['alpn'] = params['alpn'].split(',')
        
        # Параметры для Reality - извлекаем из params и добавляем в result
        if result.get('security') == 'reality':
            # pbk = publicKey (публичный ключ сервера) - обязательный
            if 'pbk' in params:
                result['pbk'] = params['pbk']
            # sid = shortId (короткий ID) - обязательный
            if 'sid' in params:
                result['sid'] = params['sid']
            # fp = fingerprint (отпечаток) - опциональный
            if 'fp' in params:
                result['fp'] = params['fp']
            # dest = destination (назначение для маскировки) - опциональный
            if 'dest' in params:
                result['dest'] = params['dest']
            
            # Также сохраняем в params для обратной совместимости
            # Это гарантирует, что параметры будут доступны через vless_params.get('params', {}).get('pbk')
        
        # Сохраняем все params для доступа через vless_params.get('params', {}).get('key')
        # Это нужно на случай, если параметры не были извлечены выше
        # Убеждаемся, что params всегда доступен
        if 'params' not in result:
            result['params'] = params
        
        return result

