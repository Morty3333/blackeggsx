"""
Тестовый скрипт для проверки парсера VLESS URL
"""
from vless_parser import VLESSURLParser
import json

# Примеры VLESS URL для тестирования
test_urls = [
    "vless://uuid@example.com:443?security=tls&sni=example.com#TestServer",
    "vless://uuid@server.com:443?type=ws&path=/path&security=tls&sni=server.com#WS-Server",
    "vless://uuid@server.com:443?type=grpc&serviceName=service&security=tls&sni=server.com#gRPC",
    "vless://uuid@server.com:443?type=tcp&security=reality&sni=example.com&pbk=publicKey&sid=shortId#Reality"
]

def test_parser():
    parser = VLESSURLParser()
    
    print("=" * 60)
    print("Тест парсера VLESS URL")
    print("=" * 60)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nТест {i}:")
        print(f"URL: {url}")
        try:
            result = parser.parse(url)
            print("✓ Парсинг успешен:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"✗ Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("Тестирование завершено")
    print("=" * 60)

if __name__ == '__main__':
    test_parser()



