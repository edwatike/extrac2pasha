import pytest
from protections import (
    detect_protection,
    get_strategy,
    apply_strategy,
    create_new_strategy
)

def test_detect_protection():
    """Тест определения типов защит"""
    # Тест капчи
    html_captcha = '<div class="g-recaptcha" data-sitekey="key"></div>'
    assert detect_protection(html_captcha) == "captcha"
    
    # Тест Cloudflare
    html_cloudflare = '<div class="cf-browser-verification"></div>'
    assert detect_protection(html_cloudflare) == "cloudflare"
    
    # Тест 403
    html_403 = '403 Forbidden'
    assert detect_protection(html_403) == "403"
    
    # Тест JS challenge
    html_js = 'javascript challenge required'
    assert detect_protection(html_js) == "js_challenge"
    
    # Тест без защиты
    html_none = '<div>Normal page</div>'
    assert detect_protection(html_none) == "none"

def test_get_strategy():
    """Тест получения стратегий"""
    # Тест существующей стратегии
    strategy = get_strategy("cloudflare")
    assert strategy is not None
    assert strategy["method"] == "cloudscraper"
    
    # Тест несуществующей стратегии
    strategy = get_strategy("nonexistent")
    assert strategy is None

def test_create_strategy():
    """Тест создания новой стратегии"""
    # Создаем новую тестовую стратегию
    create_new_strategy(
        protection_type="test_protection",
        method="selenium",
        params={
            "wait_time": 5,
            "js_enabled": True
        }
    )
    
    # Проверяем, что стратегия создана
    strategy = get_strategy("test_protection")
    assert strategy is not None
    assert strategy["method"] == "selenium"
    assert strategy["params"]["wait_time"] == 5

@pytest.mark.asyncio
async def test_apply_strategy():
    """Тест применения стратегии"""
    # Тестовый URL (можно заменить на реальный)
    test_url = "http://example.com"
    
    # Получаем стратегию для Cloudflare
    strategy = get_strategy("cloudflare")
    assert strategy is not None
    
    # Применяем стратегию
    html = apply_strategy(test_url, strategy)
    
    # Проверяем результат
    assert html is not None
    assert len(html) > 0

if __name__ == "__main__":
    pytest.main([__file__]) 