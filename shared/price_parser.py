import asyncio
import logging
import re
import random
import os
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PriceParser:
    """Класс для парсинга цен с сайтов (базовая версия)"""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    PROXY = os.getenv("PROXY", None)

    @classmethod
    def _get_headers(cls):
        return {
            'User-Agent': random.choice(cls.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        }

    @classmethod
    def _get_proxy(cls):
        if cls.PROXY:
            return {'http': cls.PROXY, 'https': cls.PROXY}
        return None

    @classmethod
    async def get_price(cls, url: str) -> Optional[float]:
        """Получает цену товара по URL"""
        logger.info(f"🔍 Парсинг URL: {url}")

        try:
            # Определяем тип сайта
            if 'wildberries.ru' in url or 'wb.ru' in url:
                return await cls._parse_wildberries(url)
            elif 'ozon.ru' in url:
                return await cls._parse_ozon(url)
            elif 'market.yandex.ru' in url:
                return await cls._parse_yandex_market(url)
            elif 'citilink.ru' in url:
                return await cls._parse_citilink(url)
            elif 'mvideo.ru' in url:
                return await cls._parse_mvideo(url)
            elif 'dns-shop.ru' in url:
                return await cls._parse_dns(url)
            else:
                return await cls._parse_generic(url)
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга {url}: {e}")
            return None

    @classmethod
    async def _fetch_html(cls, url: str) -> Optional[str]:
        """Загружает HTML страницы"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    url,
                    headers=cls._get_headers(),
                    timeout=15,
                    proxies=cls._get_proxy()
                )
            )
            if response.status_code == 200:
                return response.text
            else:
                logger.debug(f"Статус {response.status_code} для {url}")
                return None
        except Exception as e:
            logger.debug(f"Ошибка загрузки {url}: {e}")
            return None

    @classmethod
    async def _parse_ozon(cls, url: str) -> Optional[float]:
        """Парсинг Ozon"""
        html = await cls._fetch_html(url)
        if not html:
            return None

        # Ищем цену в JSON-LD
        match = re.search(r'"offers":\s*{[^}]*"price":\s*([\d.]+)', html)
        if match:
            return float(match.group(1))

        # Ищем в schema.org
        match = re.search(r'"price":\s*"([\d.]+)"', html)
        if match:
            return float(match.group(1))

        # Ищем в атрибутах
        match = re.search(r'data-price="([\d.]+)"', html)
        if match:
            return float(match.group(1))

        return None

    @classmethod
    async def _parse_wildberries(cls, url: str) -> Optional[float]:
        """Парсинг Wildberries через API"""
        try:
            # Извлекаем артикул
            article = None
            match = re.search(r'catalog/(\d+)|product/(\d+)', url)
            if match:
                article = match.group(1) or match.group(2)
            else:
                numbers = re.findall(r'\d+', url)
                if numbers:
                    article = numbers[0]

            if not article:
                return None

            # Пробуем API
            api_url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}"
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(api_url, headers=cls._get_headers(), timeout=10)
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'products' in data['data']:
                        products = data['data']['products']
                        if products:
                            price = products[0].get('salePriceU') or products[0].get('priceU')
                            if price:
                                return price / 100
            except:
                pass

            return None
        except:
            return None

    @classmethod
    async def _parse_yandex_market(cls, url: str) -> Optional[float]:
        """Парсинг Яндекс.Маркета"""
        html = await cls._fetch_html(url)
        if not html:
            return None

        match = re.search(r'"price":\s*([\d.]+)', html)
        if match:
            return float(match.group(1))

        return None

    @classmethod
    async def _parse_citilink(cls, url: str) -> Optional[float]:
        """Парсинг Citilink"""
        html = await cls._fetch_html(url)
        if not html:
            return None

        match = re.search(r'"price":\s*([\d.]+)', html)
        if match:
            return float(match.group(1))

        match = re.search(r'<span class="price">\s*([\d\s]+)\s*₽', html)
        if match:
            return float(match.group(1).replace(' ', ''))

        return None

    @classmethod
    async def _parse_mvideo(cls, url: str) -> Optional[float]:
        """Парсинг М.Видео"""
        html = await cls._fetch_html(url)
        if not html:
            return None

        match = re.search(r'"price":\s*([\d.]+)', html)
        if match:
            return float(match.group(1))

        return None

    @classmethod
    async def _parse_dns(cls, url: str) -> Optional[float]:
        """Парсинг DNS"""
        html = await cls._fetch_html(url)
        if not html:
            return None

        match = re.search(r'"price":\s*([\d.]+)', html)
        if match:
            return float(match.group(1))

        match = re.search(r'<span class="price">\s*([\d\s]+)\s*₽', html)
        if match:
            return float(match.group(1).replace(' ', ''))

        return None

    @classmethod
    async def _parse_generic(cls, url: str) -> Optional[float]:
        """Универсальный парсер"""
        html = await cls._fetch_html(url)
        if not html:
            return None

        patterns = [
            r'(\d+[\s\d]*)\s?[₽$€]',
            r'[₽$€]\s?(\d+[\s\d]*)',
            r'цена[:\s]+(\d+[\s\d]*)',
            r'(\d+[\s\d]*)\s?руб',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(' ', '')
                try:
                    return float(price_str)
                except:
                    continue

        return None


# ========== ТЕСТИРОВАНИЕ ==========

async def test_parser(url: str = None):
    if url:
        print(f"\n🔍 Тестирование URL: {url}")
        price = await PriceParser.get_price(url)
        if price:
            print(f"✅ Цена: {price:,.0f} ₽")
        else:
            print("❌ Не удалось получить цену")
        return

    test_urls = [
        ("Wildberries", "https://www.wildberries.ru/catalog/218675291/detail.aspx"),
        ("Ozon", "https://www.ozon.ru/product/noutbuk-honor-magicbook-x14-2024-16-512-ssd-intel-core-i5-12450h-integrirovannaya-intel-uhd-1795400301/"),
    ]

    print("🧪 Тестирование парсера цен...\n")

    for name, test_url in test_urls:
        print(f"📦 {name}: {test_url}")
        price = await PriceParser.get_price(test_url)
        if price:
            print(f"   ✅ Цена: {price:,.0f} ₽\n")
        else:
            print(f"   ❌ Не удалось получить цену\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        asyncio.run(test_parser(sys.argv[1]))
    else:
        asyncio.run(test_parser())
