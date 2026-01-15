import os
import logging
import requests
import re
from flask import Flask
from bs4 import BeautifulSoup
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

def parse_black_russia_funpay():
    """РАБОЧИЙ парсинг для FunPay"""
    try:
        url = "https://funpay.com/chips/186/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        logger.info("🎯 Парсинг Black Russia на FunPay...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP ошибка: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем ВСЕ карточки товаров
        cards = soup.find_all('a', class_='tc-item')
        logger.info(f"📦 Найдено карточек товаров: {len(cards)}")
        
        items = []
        
        # Обрабатываем первые 30 карточек
        for card in cards[:30]:
            try:
                # 1. Извлекаем название
                title_elem = card.find('div', class_='tc-desc-text')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # 2. Фильтруем ТОЛЬКО Black Russia
                title_lower = title.lower()
                keywords = ['black russia', 'blackrussia', 'блек раша', 'блэк раша']
                
                if not any(keyword in title_lower for keyword in keywords):
                    continue
                
                # 3. Извлекаем цену (правильный способ)
                price_elem = card.find('div', class_='tc-price')
                if not price_elem:
                    continue
                
                # Получаем весь текст из блока цены
                price_text = price_elem.get_text(strip=True)
                
                # Извлекаем цифры из цены
                # Форматы: "100 руб", "100₽", "100 р."
                price_match = re.search(r'(\d+[\s ]*\d*)\s*(?:руб|₽|р\.)', price_text)
                if price_match:
                    # Убираем пробелы и неразрывные пробелы
                    price_str = price_match.group(1).replace(' ', '').replace(' ', '')
                    price = int(price_str)
                else:
                    # Альтернативный поиск: просто все цифры
                    digits = re.findall(r'\d+', price_text.replace(' ', ''))
                    if not digits:
                        continue
                    price = int(''.join(digits))
                
                # Фильтр по цене
                if price < 10 or price > 50000:
                    continue
                
                # 4. Извлекаем ссылку
                href = card.get('href', '')
                if href.startswith('/'):
                    link = f"https://funpay.com{href}"
                else:
                    link = href
                
                # 5. Проверяем онлайн статус (по атрибуту data-online)
                seller_online = card.get('data-online') == '1'
                
                # 6. Извлекаем ID продавца
                seller_id = card.get('data-user', '')
                
                items.append({
                    'title': title[:100],
                    'price': price,
                    'link': link,
                    'seller_online': seller_online,
                    'seller_id': seller_id,
                    'raw_price_text': price_text  # Для отладки
                })
                
                logger.info(f"   ✅ '{title[:50]}...' - {price} руб. | {'🟢 Онлайн' if seller_online else '🔴 Офлайн'}")
                
            except Exception as e:
                logger.warning(f"⚠️ Ошибка обработки карточки: {e}")
                continue
        
        logger.info(f"🎯 Найдено товаров Black Russia: {len(items)}")
        return items
        
    except Exception as e:
        logger.error(f"💥 Ошибка парсинга: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def debug_page_structure():
    """Анализ структуры страницы"""
    try:
        url = "https://funpay.com/chips/186/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        logger.info("🔍 Анализ структуры страницы...")
        response = requests.get(url, headers=headers, timeout=15)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим первую карточку для анализа
        first_card = soup.find('a', class_='tc-item')
        
        if first_card:
            logger.info("📋 Структура первой карточки:")
            
            # Показываем все классы
            logger.info(f"   Классы: {first_card.get('class', [])}")
            
            # Показываем все data-атрибуты
            for attr, value in first_card.attrs.items():
                if attr.startswith('data-'):
                    logger.info(f"   {attr}: {value}")
            
            # Ищем заголовок
            title_elem = first_card.find('div', class_='tc-desc-text')
            if title_elem:
                logger.info(f"   Заголовок: {title_elem.get_text(strip=True)[:100]}")
            
            # Ищем цену и показываем полный HTML
            price_elem = first_card.find('div', class_='tc-price')
            if price_elem:
                logger.info(f"   HTML цены: {price_elem}")
                logger.info(f"   Текст цены: '{price_elem.get_text(strip=True)}'")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка анализа: {e}")
        return False

# Маршруты Flask
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>FunPay Hunter - Исправленная версия</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            .btn { display: inline-block; padding: 10px 20px; margin: 5px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .btn-green { background: #28a745; }
            .btn-orange { background: #fd7e14; }
        </style>
    </head>
    <body>
        <h1>🎯 FunPay Hunter - Исправленная версия</h1>
        <p><strong>Статус:</strong> ✅ Сервер работает</p>
        <p><strong>Время:</strong> ''' + datetime.now().strftime("%H:%M:%S") + '''</p>
        
        <h3>Действия:</h3>
        <a href="/parse" class="btn">🔍 Запустить парсинг</a>
        <a href="/debug" class="btn btn-orange">🛠️ Анализ структуры</a>
        
        <h3>Что нового:</h3>
        <ul>
            <li>✅ Правильный поиск карточек по <code>a.tc-item</code></li>
            <li>✅ Извлечение цены из <code>div.tc-price</code></li>
            <li>✅ Проверка онлайн статуса через <code>data-online</code></li>
            <li>✅ Фильтр только Black Russia</li>
        </ul>
    </body>
    </html>
    '''

@app.route('/parse')
def parse_page():
    """Страница парсинга"""
    items = parse_black_russia_funpay()
    
    if items:
        result = f"<h2>✅ Найдено {len(items)} товаров Black Russia:</h2>"
        
        for item in items:
            online_badge = "🟢 ОНЛАЙН" if item['seller_online'] else "🔴 ОФФЛАЙН"
            result += f'''
            <div style="border:1px solid #ddd; padding:15px; margin:10px; border-radius:5px;">
                <h4>{item['title']}</h4>
                <p><strong>Цена:</strong> {item['price']} руб. ({item['raw_price_text']})</p>
                <p><strong>Статус продавца:</strong> {online_badge}</p>
                <p><strong>ID продавца:</strong> {item['seller_id']}</p>
                <p><a href="{item['link']}" target="_blank">Открыть на FunPay</a></p>
            </div>
            '''
    else:
        result = '''
        <div style="background:#f8d7da; padding:20px; border-radius:5px;">
            <h2>❌ Товары не найдены</h2>
            <p>Парсер не нашел товаров Black Russia.</p>
            <p>Попробуйте <a href="/debug">проанализировать структуру</a>.</p>
        </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Результаты парсинга</title></head>
    <body style="font-family:Arial; margin:20px;">
        <a href="/">← Назад</a>
        {result}
    </body>
    </html>
    '''

@app.route('/debug')
def debug_page():
    """Страница отладки структуры"""
    debug_page_structure()
    
    return '''
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial; margin:20px;">
        <a href="/">← Назад</a>
        <h2>✅ Анализ структуры выполнен</h2>
        <p>Проверьте логи в Render Dashboard (вкладка Logs).</p>
        <p>Там будет детальная информация о структуре карточек товаров.</p>
        <p><a href="/parse">Запустить парсинг →</a></p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return "OK"

# Запуск приложения
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
