"""
Модуль для генерации конфигурации Xray
"""
import json
from typing import Dict


class XrayConfigGenerator:
    """Генератор конфигурации для Xray"""
    
    @staticmethod
    def generate(vless_params: Dict[str, any], local_port: int = 10808, 
                 socks_port: int = 10809) -> Dict:
        """
        Генерирует конфигурацию Xray на основе параметров VLESS
        
        Args:
            vless_params: Параметры из парсера VLESS URL
            local_port: Локальный порт для HTTP прокси
            socks_port: Локальный порт для SOCKS5 прокси
        """
        config = {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "port": local_port,
                    "protocol": "http",
                    "settings": {
                        "udp": True
                    },
                    "tag": "http"
                },
                {
                    "port": socks_port,
                    "protocol": "socks",
                    "settings": {
                        "udp": True,
                        "auth": "noauth"
                    },
                    "tag": "socks"
                }
            ],
            "outbounds": [
                {
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": vless_params['host'],
                                "port": vless_params['port'],
                                "users": [
                                    {
                                        "id": vless_params['uuid'],
                                        "encryption": vless_params.get('encryption', 'none'),
                                        "flow": vless_params.get('flow', '')
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": XrayConfigGenerator._generate_stream_settings(vless_params),
                    "tag": "proxy"
                },
                {
                    "protocol": "freedom",
                    "tag": "direct"
                }
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {
                        "type": "field",
                        "ip": [
                            "geoip:private"
                        ],
                        "outboundTag": "direct"
                    }
                ]
            }
        }
        
        return config
    
    @staticmethod
    def _generate_stream_settings(vless_params: Dict[str, any]) -> Dict:
        """Генерирует настройки потока в зависимости от типа"""
        stream_type = vless_params.get('type', 'tcp')
        security = vless_params.get('security', 'none')
        
        stream_settings = {
            "network": stream_type
        }
        
        # Настройки TLS
        if security in ['tls', 'reality']:
            tls_settings = {
                "allowInsecure": False,
                "serverName": vless_params.get('sni', vless_params['host'])
            }
            
            if 'alpn' in vless_params:
                tls_settings["alpn"] = vless_params['alpn']
            
            if security == 'reality':
                # Проверяем наличие обязательных параметров для Reality
                # Пробуем разные способы получения параметров
                pbk = (vless_params.get('pbk') or 
                       vless_params.get('params', {}).get('pbk') or
                       vless_params.get('params', {}).get('pbk', ''))
                
                sid = (vless_params.get('sid') or 
                      vless_params.get('params', {}).get('sid') or
                      vless_params.get('params', {}).get('sid', ''))
                
                # Если параметры не найдены, пробуем извлечь из params напрямую
                if not pbk and 'params' in vless_params:
                    pbk = vless_params['params'].get('pbk', '')
                if not sid and 'params' in vless_params:
                    sid = vless_params['params'].get('sid', '')
                
                if not pbk or not sid:
                    error_msg = (
                        f"Для Reality требуются обязательные параметры: pbk (publicKey) и sid (shortId).\n"
                        f"Найдено: pbk={'есть (' + pbk[:20] + '...)' if pbk else 'нет'}, "
                        f"sid={'есть (' + sid + ')' if sid else 'нет'}\n"
                        f"Доступные параметры: {list(vless_params.keys())}"
                    )
                    raise ValueError(error_msg)
                
                # Создаем конфигурацию Reality
                reality_config = {
                    "show": False,
                    "xver": 0,
                    "publicKey": str(pbk).strip()  # Обязательный параметр
                }
                
                # Short ID (sid в URL) - обязательный параметр
                if sid:
                    sid_str = str(sid).strip()
                    # Может быть несколько через запятую
                    if ',' in sid_str:
                        reality_config["shortId"] = [s.strip() for s in sid_str.split(',')]
                    else:
                        reality_config["shortId"] = [sid_str]
                
                # Server names (sni в URL) - обязательный параметр
                sni_value = (vless_params.get('sni') or 
                            vless_params.get('params', {}).get('sni') or 
                            vless_params.get('host', ''))
                
                if not sni_value:
                    sni_value = vless_params.get('host', '')
                
                if sni_value:
                    sni_str = str(sni_value).strip()
                    if ',' in sni_str:
                        reality_config["serverNames"] = [s.strip() for s in sni_str.split(',')]
                    else:
                        reality_config["serverNames"] = [sni_str]
                else:
                    # Если нет sni, используем host
                    reality_config["serverNames"] = [str(vless_params.get('host', '')).strip()]
                
                # Fingerprint (fp в URL) - опциональный
                fp = (vless_params.get('fp') or 
                     vless_params.get('params', {}).get('fp') or
                     vless_params.get('params', {}).get('fp', ''))
                
                if fp and str(fp).strip():
                    reality_config["fingerprint"] = str(fp).strip()
                
                # Убеждаемся, что конфигурация не пустая
                if not reality_config.get("publicKey") or not reality_config.get("shortId"):
                    raise ValueError(
                        f"Конфигурация Reality неполная: publicKey={bool(reality_config.get('publicKey'))}, "
                        f"shortId={bool(reality_config.get('shortId'))}"
                    )
                
                tls_settings["reality"] = reality_config
            
            stream_settings["security"] = security
            stream_settings["tlsSettings"] = tls_settings
        
        # Настройки для WebSocket
        if stream_type == 'ws':
            ws_settings = {
                "path": vless_params.get('path', '/')
            }
            if 'host_header' in vless_params:
                ws_settings["headers"] = {
                    "Host": vless_params['host_header']
                }
            stream_settings["wsSettings"] = ws_settings
        
        # Настройки для gRPC
        elif stream_type == 'grpc':
            stream_settings["grpcSettings"] = {
                "serviceName": vless_params.get('serviceName', '')
            }
        
        # Настройки для TCP
        elif stream_type == 'tcp':
            header_type = vless_params.get('headerType', 'none')
            if header_type != 'none':
                tcp_settings = {
                    "header": {
                        "type": header_type
                    }
                }
                stream_settings["tcpSettings"] = tcp_settings
        
        return stream_settings
    
    @staticmethod
    def save_config(config: Dict, filepath: str = 'config.json'):
        """Сохраняет конфигурацию в JSON файл"""
        # Проверяем конфигурацию Reality перед сохранением
        try:
            outbounds = config.get('outbounds', [])
            for outbound in outbounds:
                if outbound.get('protocol') == 'vless':
                    stream_settings = outbound.get('streamSettings', {})
                    if stream_settings.get('security') == 'reality':
                        reality_settings = stream_settings.get('tlsSettings', {}).get('reality', {})
                        if not reality_settings or not reality_settings.get('publicKey'):
                            raise ValueError(
                                "Конфигурация Reality неполная: отсутствует publicKey в realitySettings"
                            )
        except Exception as e:
            raise ValueError(f"Ошибка проверки конфигурации перед сохранением: {e}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

