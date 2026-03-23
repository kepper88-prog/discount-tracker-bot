import requests
from bs4 import BeautifulSoup
import logging
import re

logger = logging.getLogger(__name__)

class PriceParser:
    """Класс для парсинга цен с сайтов"""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    @classmethod
    async def get_price(cls, url: str) -> float | None:
        """
        Получает цену товара по URL
        Возвращает цену или None, если не удалось получить
        """
        try:
            # Определяем сайт и выбираем стратегию парсинга
            if 'wildberries.ru' in url:
                return await cls._parse_wildberries(url)
            elif 'ozon.ru' in url:
                return await cls._parse_ozon(url)
            else:
                # Универсальный парсер для любых сайтов
                return await cls._parse_generic(url)
        except Exception as e:
            logger.error(f"Ошибка парсинга {url}: {e}")
            return None
    
    @classmethod
    async def _parse_wildberries(cls, url: str) -> float | None:
        """Парсинг Wildberries через API"""
        # Извлекаем артикул из URL
        match = re.search(r'(\d+)', url.split('/')[-1])
        if not match:
            return None
        
        article = match.group(1)
        api_url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}"
        
        response = requests.get(api_url, headers=cls.HEADERS, timeout=10)
        data = response.json()
        
        try:
            price = data['data']['products'][0]['salePriceU'] / 100  # WB хранит цены в копейках
            return float(price)
        except (KeyError, IndexError):
            return None
    
    @classmethod
    async def _parse_ozon(cls, url: str) -> float | None:
        """Парсинг Ozon"""
        response = requests.get(url, headers=cls.HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем цену по разным селекторам
        price_selectors = [
            '[data-widget="webPrice"]',  # Основной виджет цены
            '.ui-c8',  # Стандартный класс цены
            '[itemprop="price"]'  # Микроразметка
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text()
                # Извлекаем число из текста
                numbers = re.findall(r'[\d\s]+', price_text.replace(' ', ''))
                if numbers:
                    return float(numbers[0].replace(' ', ''))
        return None
    
    @classmethod
    async def _parse_generic(cls, url: str) -> float | None:
        """Универсальный парсер для любых сайтов"""
        response = requests.get(url, headers=cls.HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем цену по частым паттернам
        patterns = [
            r'(\d+[\s\d]*)\s?[₽$€]',  # 1 999 ₽
            r'[₽$€]\s?(\d+[\s\d]*)',  # ₽ 1 999
            r'цена[:\s]+(\d+[\s\d]*)',  # цена: 1999
            r'(\d+[\s\d]*)\s?руб'  # 1999 руб
        ]
        
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(' ', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        return None