# ==============================================================================
# GERENCIAMENTO DO NAVEGADOR (SELENIUM WEBDRIVER)
# ==============================================================================
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

from config import BROWSER_CONFIG, SCREENSHOTS_DIR, TIMEZONE

logger = logging.getLogger("BotReserva")


def criar_driver(headless: Optional[bool] = None) -> webdriver.Remote:
    """
    Inicializa e configura uma instância do Selenium WebDriver.
    Tenta primeiro o Google Chrome; se falhar, tenta o Microsoft Edge.
    """
    is_headless = headless if headless is not None else BROWSER_CONFIG.get("headless", False)

    # 1. Tentativa com Google Chrome
    try:
        chrome_options = ChromeOptions()
        if is_headless:
            chrome_options.add_argument("--headless=new")
        else:
            chrome_options.add_experimental_option("detach", True)
        
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1366,768")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(BROWSER_CONFIG["timeout_segundos"])
        logger.info("Navegador Google Chrome inicializado com sucesso.")
        return driver
    except Exception as erro_chrome:
        logger.warning(f"Google Chrome não inicializou ({erro_chrome}). Tentando Microsoft Edge...")

    # 2. Fallback: Microsoft Edge
    try:
        edge_options = EdgeOptions()
        if is_headless:
            edge_options.add_argument("--headless=new")
        else:
            edge_options.add_experimental_option("detach", True)
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--disable-notifications")
        edge_options.add_argument("--window-size=1366,768")

        driver = webdriver.Edge(options=edge_options)
        driver.set_page_load_timeout(BROWSER_CONFIG["timeout_segundos"])
        logger.info("Navegador Microsoft Edge inicializado com sucesso.")
        return driver
    except Exception as erro_edge:
        logger.error(f"Falha crítica ao inicializar navegadores: Chrome={erro_chrome} | Edge={erro_edge}")
        raise RuntimeError("Não foi possível iniciar nenhum navegador compatível (Chrome ou Edge).")


def salvar_screenshot(driver: webdriver.Remote, prefixo: str = "erro") -> Optional[Path]:
    """
    Salva uma captura de tela com o formato de nome:
    screenshots/{prefixo}_YYYY-MM-DD_HH-MM-SS.png
    """
    try:
        agora = datetime.now(TIMEZONE)
        timestamp_str = agora.strftime("%Y-%m-%d_%H-%M-%S")
        nome_arquivo = f"{prefixo}_{timestamp_str}.png"
        caminho = SCREENSHOTS_DIR / nome_arquivo
        
        driver.save_screenshot(str(caminho))
        logger.info(f"Captura de tela salva em: {caminho}")
        return caminho
    except Exception as e:
        logger.error(f"Falha ao salvar captura de tela: {e}")
        return None
