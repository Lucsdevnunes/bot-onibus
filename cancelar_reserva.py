# ==============================================================================
# BOT DE CANCELAMENTO DE RESERVA POR NOME (MAURILÂNDIA/GO)
# ==============================================================================
import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from browser import criar_driver, salvar_screenshot
from config import BROWSER_CONFIG, LOG_FILE, SITE_URL, TIMEZONE

logger = logging.getLogger("BotCancelamento")


def configurar_logger():
    """Configura o logger para console e logs/bot.log"""
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    formato = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formato)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formato)
    logger.addHandler(console_handler)
    return logger


class AutomacaoCancelamento:
    """
    Classe responsável por localizar e cancelar reservas de alunos pelo Nome e Data de amanhã.
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.timeout = BROWSER_CONFIG.get("timeout_segundos", 15)
        self.wait = WebDriverWait(self.driver, self.timeout, poll_frequency=0.1)

    @staticmethod
    def calcular_data_viagem() -> Tuple[str, str]:
        """Calcula a data do dia seguinte (amanhã). Retorna (DD/MM/AAAA, AAAA-MM-DD)."""
        agora = datetime.now(TIMEZONE)
        amanha = agora + timedelta(days=1)
        return amanha.strftime("%d/%m/%Y"), amanha.strftime("%Y-%m-%d")

    def abrir_site(self) -> bool:
        """Abre a página do sistema."""
        try:
            logger.info(f"Abrindo interface do sistema: {SITE_URL}")
            self.driver.get(SITE_URL)
            self.wait.until(EC.presence_of_element_located((By.ID, "date")))
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar o site: {e}")
            salvar_screenshot(self.driver, "erro_carregamento_cancelamento")
            return False

    def cancelar_por_nome(self, nome_aluno: str, data_iso: str, data_br: str) -> Tuple[bool, str]:
        """
        Localiza a reserva do aluno pelo nome e data de amanhã e efetua o cancelamento.
        """
        try:
            logger.info("=" * 65)
            logger.info(f"SOLICITAÇÃO DE CANCELAMENTO:")
            logger.info(f"Nome do Aluno: '{nome_aluno}'")
            logger.info(f"Data da Viagem: {data_br} ({data_iso})")
            logger.info("=" * 65)

            # 1. Rola até a seção de consulta e cancelamento
            self.driver.execute_script(
                """
                const sec = document.querySelector('#reservation-management');
                if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'center' });
                """
            )
            time.sleep(0.5)

            # 2. Localiza os campos de Nome e Data na área "Não lembro o código?"
            input_nome = self.wait.until(EC.presence_of_element_located((By.ID, "lookup-name-only")))
            input_data = self.wait.until(EC.presence_of_element_located((By.ID, "lookup-date")))
            btn_localizar = self.wait.until(EC.element_to_be_clickable((By.ID, "lookup-name-button")))

            # 3. Preenche o Nome e a Data via DOM
            self.driver.execute_script(
                """
                const nameInp = document.querySelector('#lookup-name-only');
                const dateInp = document.querySelector('#lookup-date');
                if (nameInp) {
                    nameInp.value = arguments[0];
                    nameInp.dispatchEvent(new Event('input', { bubbles: true }));
                    nameInp.dispatchEvent(new Event('change', { bubbles: true }));
                }
                if (dateInp) {
                    dateInp.value = arguments[1];
                    dateInp.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                nome_aluno.strip(),
                data_iso,
            )
            time.sleep(0.3)

            # 4. Clica no botão "🔍 Localizar minha reserva"
            logger.info("Localizando reserva ativa no sistema...")
            self.driver.execute_script("arguments[0].click();", btn_localizar)

            # 5. Aguarda o resultado no elemento #lookup-result
            self.wait.until(
                lambda d: len(d.find_element(By.ID, "lookup-result").text.strip()) > 0
            )
            time.sleep(0.8)

            resultado_elem = self.driver.find_element(By.ID, "lookup-result")
            texto_resultado = resultado_elem.text.strip()

            # Se nenhuma reserva for encontrada
            if "Nenhuma reserva ativa foi encontrada" in texto_resultado or "não encontrada" in texto_resultado.lower():
                logger.warning(f"❌ Nenhuma reserva ativa foi encontrada para '{nome_aluno}' na data {data_br}.")
                salvar_screenshot(self.driver, "cancelamento_nao_encontrado")
                return False, f"Nenhuma reserva ativa encontrada para {nome_aluno} em {data_br}."

            # 6. Sobrescreve o window.confirm para aceitar a confirmação automaticamente sem travar o navegador
            self.driver.execute_script("window.confirm = function() { return true; };")

            # 7. Localiza o botão "❌ Cancelar esta reserva"
            botoes_cancelar = resultado_elem.find_elements(By.CSS_SELECTOR, ".cancel-by-name")
            if not botoes_cancelar:
                # Tenta botão alternativo de cancelamento
                botoes_cancelar = self.driver.find_elements(By.CSS_SELECTOR, "#cancel-my-reservation, .cancel-button")

            if not botoes_cancelar:
                logger.error("Botão de cancelamento não foi encontrado na reserva localizada.")
                salvar_screenshot(self.driver, "erro_botao_cancelar_nao_encontrado")
                return False, "Botão de cancelamento não encontrado."

            btn_cancelar = botoes_cancelar[0]
            logger.info("Reserva localizada! Acionando cancelamento...")
            self.driver.execute_script("arguments[0].click();", btn_cancelar)

            # 8. Aguarda a confirmação de cancelamento no resultado
            self.wait.until(
                lambda d: "cancelada com sucesso" in d.find_element(By.ID, "lookup-result").text.lower()
                or "erro" in d.find_element(By.ID, "lookup-result").get_attribute("innerHTML").lower()
            )
            time.sleep(0.5)

            msg_final = self.driver.find_element(By.ID, "lookup-result").text.strip()

            if "cancelada com sucesso" in msg_final.lower():
                logger.info("=" * 65)
                logger.info(f"✅ SUCESSO: A reserva de '{nome_aluno}' foi CANCELADA com êxito!")
                logger.info("=" * 65)
                salvar_screenshot(self.driver, "sucesso_cancelamento")
                return True, "Reserva cancelada com sucesso!"
            else:
                logger.error(f"Erro ao cancelar: {msg_final}")
                salvar_screenshot(self.driver, "erro_cancelamento_final")
                return False, msg_final

        except Exception as e:
            logger.error(f"Falha durante o processo de cancelamento: {e}")
            salvar_screenshot(self.driver, "excecao_cancelamento")
            return False, str(e)


def processar_cancelamento(nome_aluno: str, manter_aberto: bool = True) -> bool:
    """Executa o fluxo completo de cancelamento para um aluno."""
    driver = None
    sucesso = False
    try:
        driver = criar_driver(headless=False)
        bot = AutomacaoCancelamento(driver)
        data_br, data_iso = bot.calcular_data_viagem()

        if not bot.abrir_site():
            return False

        sucesso, _ = bot.cancelar_por_nome(nome_aluno, data_iso, data_br)
        return sucesso
    finally:
        if driver:
            if manter_aberto:
                logger.info("Tela do navegador mantida aberta para sua conferência.")
            else:
                try:
                    driver.quit()
                except Exception:
                    pass


def main():
    configurar_logger()
    parser = argparse.ArgumentParser(description="Bot para Cancelar Reserva de Aluno por Nome")
    parser.add_argument("nome", nargs="?", help="Nome completo do aluno que solicitou cancelamento")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("      BOT DE CANCELAMENTO DE RESERVA POR NOME (MAURILÂNDIA)")
    print("=" * 65 + "\n")

    nome = args.nome
    while True:
        if not nome:
            nome = input("👉 Digite o NOME COMPLETO do aluno para cancelar (ou 'sair'): ").strip()

        if not nome or nome.lower() in ["sair", "exit", "q"]:
            print("Encerrando bot de cancelamento.")
            break

        sucesso = processar_cancelamento(nome, manter_aberto=True)

        print("\n" + "-" * 65)
        outro = input("Deseja cancelar a reserva de outro aluno? (s/n): ").strip().lower()
        if outro in ["s", "sim", "y"]:
            nome = None
        else:
            print("Processo finalizado com sucesso!")
            break


if __name__ == "__main__":
    main()
