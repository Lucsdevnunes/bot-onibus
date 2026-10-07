# ==============================================================================
# MÓDULO DE AUTOMAÇÃO DA RESERVA (CONTINUIDADE, RETOMADA E REFRESH ATIVO)
# ==============================================================================
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from browser import salvar_screenshot
from config import BROWSER_CONFIG, ONIBUS_CONFIG, PASSAGEIROS, SITE_URL, TIMEZONE

logger = logging.getLogger("BotReserva")


class AutomacaoReserva:
    """
    Classe responsável pela execução sequencial, contínua e incremental
    das reservas de passageiros com espera ativa/refresh até a abertura dos assentos.
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.timeout = BROWSER_CONFIG["timeout_segundos"]
        self.wait = WebDriverWait(self.driver, self.timeout, poll_frequency=0.05)

    @staticmethod
    def calcular_data_viagem() -> Tuple[str, str, datetime]:
        """
        Calcula automaticamente a data da viagem (SEMPRE o dia seguinte no fuso de São Paulo).
        Retorna (DD/MM/AAAA, AAAA-MM-DD, datetime_amanha).
        """
        agora = datetime.now(TIMEZONE)
        amanha = agora + timedelta(days=1)
        data_br = amanha.strftime("%d/%m/%Y")
        data_iso = amanha.strftime("%Y-%m-%d")
        return data_br, data_iso, amanha

    def abrir_site(self) -> bool:
        """
        Abre a página da reserva e aguarda a prontidão do DOM.
        """
        try:
            logger.info(f"Carregando interface: {SITE_URL}")
            self.driver.get(SITE_URL)
            self.wait.until(EC.presence_of_element_located((By.ID, "date")))
            self.wait.until(EC.presence_of_element_located((By.ID, "bus-list")))
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar o site: {e}")
            salvar_screenshot(self.driver, "erro_carregamento_site")
            return False

    def preencher_data(self, data_br: str, data_iso: str) -> bool:
        """
        Seleciona a data de amanhã instantaneamente via DOM e sincroniza o estado.
        """
        try:
            self.driver.execute_script(
                """
                const dInput = document.querySelector('#date');
                const dCal = document.querySelector('#date-calendar');
                if (dInput) {
                    dInput.value = arguments[0];
                    dInput.dispatchEvent(new Event('input', { bubbles: true }));
                    dInput.dispatchEvent(new Event('change', { bubbles: true }));
                    dInput.dispatchEvent(new Event('blur', { bubbles: true }));
                }
                if (dCal) {
                    dCal.value = arguments[1];
                    dCal.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                data_br,
                data_iso,
            )

            # Aguarda a renderização dos ônibus
            self.wait.until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "#bus-list .bus")) > 0
            )
            return True
        except Exception as e:
            logger.error(f"Falha ao selecionar a data: {e}")
            salvar_screenshot(self.driver, "erro_selecao_data")
            return False

    def aguardar_e_recarregar_ate_abertura(self, data_br: str, data_iso: str) -> bool:
        """
        Se as vagas da data de amanhã ainda estiverem fechadas/bloqueadas,
        recarrega a página e tenta novamente em loop contínuo até as vagas abrirem!
        Só para o refresh quando o ônibus 0542 estiver aberto para novas reservas.
        """
        numero_alvo = ONIBUS_CONFIG["numero"]
        logger.info(f"Verificando liberação de vagas para o dia seguinte ({data_br}) no ônibus {numero_alvo}...")

        while True:
            try:
                # Garante que a data de amanhã esteja aplicada
                self.preencher_data(data_br, data_iso)

                # Localiza o card do ônibus 0542
                botoes = self.driver.find_elements(By.CSS_SELECTOR, "#bus-list .bus")
                card_0542 = None
                for b in botoes:
                    if numero_alvo in b.text:
                        card_0542 = b
                        break

                msg_el = self.driver.find_element(By.ID, "message")
                msg_texto = msg_el.text.lower() if msg_el else ""

                card_classes = (card_0542.get_attribute("class") or "") if card_0542 else ""
                card_texto = card_0542.text.lower() if card_0542 else ""

                # Verifica se o ônibus ou o sistema ainda estão com reservas bloqueadas
                esta_fechado = (
                    "locked" in card_classes
                    or "fechadas" in card_texto
                    or "encerradas" in msg_texto
                    or "não está aberta" in msg_texto
                    or "fechadas" in msg_texto
                )

                if not esta_fechado and card_0542:
                    logger.info("=" * 65)
                    logger.info("🎉 [VAGAS LIBERADAS!] O sistema abriu para novas reservas!")
                    logger.info("=" * 65)
                    return True

                logger.info(
                    f"[🔒 AGUARDANDO ABERTURA] As reservas de amanhã ainda estão fechadas no site. "
                    f"Recarregando e tentando novamente..."
                )
                time.sleep(0.5)

                # Dá refresh na página para buscar novos dados do backend
                self.driver.refresh()
                self.wait.until(EC.presence_of_element_located((By.ID, "date")))
                self.wait.until(EC.presence_of_element_located((By.ID, "bus-list")))

            except Exception as e:
                logger.warning(f"Aguardando resposta do servidor: {e}")
                time.sleep(0.5)

    def selecionar_onibus(self, numero_alvo: str, motorista_alvo: str) -> bool:
        """
        Localiza e seleciona especificamente o ônibus 0542.
        """
        try:
            self.wait.until(
                lambda d: any(
                    numero_alvo in b.text for b in d.find_elements(By.CSS_SELECTOR, "#bus-list .bus")
                )
            )

            botoes_onibus = self.driver.find_elements(By.CSS_SELECTOR, "#bus-list .bus")
            onibus_alvo = None
            for btn in botoes_onibus:
                if numero_alvo in btn.text:
                    onibus_alvo = btn
                    break

            if not onibus_alvo:
                logger.error(f"Ônibus {numero_alvo} não encontrado.")
                salvar_screenshot(self.driver, "erro_onibus_nao_encontrado")
                return False

            classes = onibus_alvo.get_attribute("class") or ""
            texto = onibus_alvo.text

            if "full" in classes or "LOTADO" in texto.upper():
                logger.error(f"Ônibus {numero_alvo} está LOTADO.")
                salvar_screenshot(self.driver, "erro_onibus_lotado")
                return False

            # Clica no ônibus para exibir o mapa de poltronas
            self.driver.execute_script("arguments[0].click();", onibus_alvo)
            return True
        except Exception as e:
            logger.error(f"Falha ao selecionar ônibus {numero_alvo}: {e}")
            salvar_screenshot(self.driver, "erro_selecao_onibus")
            return False

    def selecionar_poltrona(
        self,
        poltrona_preferencial: int,
        nome_usuario: str,
        poltronas_ja_reservadas: List[int],
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Localiza a poltrona denominada para o passageiro.
        Se ocupada, busca a poltrona livre mais próxima (ordem de proximidade decrescente/crescente).
        """
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "seat-section")))
            self.wait.until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "#seat-map .seat")) >= 40
            )

            botoes_poltronas = self.driver.find_elements(By.CSS_SELECTOR, "#seat-map .seat")
            mapa_poltronas: Dict[int, WebElement] = {}

            for btn in botoes_poltronas:
                spans = btn.find_elements(By.CSS_SELECTOR, ".seat-number")
                num_texto = spans[0].text.strip() if spans else btn.text.split("\n")[0].strip()
                if num_texto.isdigit():
                    mapa_poltronas[int(num_texto)] = btn

            # 1. Verifica se o aluno já possui reserva registrada nesta poltrona ou outra
            partes_nome = nome_usuario.strip().lower().split()
            primeiro_nome = partes_nome[0] if partes_nome else ""

            if primeiro_nome and "aluno" not in primeiro_nome:
                for num_p, btn in mapa_poltronas.items():
                    texto_p = btn.text.lower()
                    title_p = (btn.get_attribute("title") or "").lower()
                    if primeiro_nome in texto_p or primeiro_nome in title_p:
                        logger.info(f"'{nome_usuario}' já possui reserva confirmada na poltrona {num_p}.")
                        return True, "JA_RESERVADO", num_p

            # 2. Ordem de busca: primeiro a denominada; depois as mais próximas em ordem decrescente/crescente
            ordem_tentativa = [poltrona_preferencial]
            for p in range(poltrona_preferencial - 1, 0, -1):
                ordem_tentativa.append(p)
            for p in range(poltrona_preferencial + 1, 49):
                if p not in ordem_tentativa:
                    ordem_tentativa.append(p)

            poltrona_escolhida = None
            btn_escolhido = None

            for p_candidata in ordem_tentativa:
                if p_candidata in poltronas_ja_reservadas:
                    continue

                btn_candidato = mapa_poltronas.get(p_candidata)
                if not btn_candidato:
                    continue

                classes = btn_candidato.get_attribute("class") or ""
                is_disabled = not btn_candidato.is_enabled()

                if "occupied" not in classes and not is_disabled and "locked-view" not in classes:
                    poltrona_escolhida = p_candidata
                    btn_escolhido = btn_candidato
                    break

            if not poltrona_escolhida or not btn_escolhido:
                logger.error(f"Nenhuma poltrona disponível para '{nome_usuario}'.")
                salvar_screenshot(self.driver, "erro_sem_poltronas")
                return False, "SEM_VAGAS", None

            if poltrona_escolhida == poltrona_preferencial:
                logger.info(f"Poltrona denominada {poltrona_preferencial} DISPONÍVEL para '{nome_usuario}'.")
            else:
                logger.warning(
                    f"Poltrona denominada {poltrona_preferencial} estava ocupada. "
                    f"Alocando a livre mais próxima: Poltrona {poltrona_escolhida} para '{nome_usuario}'."
                )

            # Clica no assento escolhido
            self.driver.execute_script("arguments[0].click();", btn_escolhido)
            return True, "SELECIONADA", poltrona_escolhida

        except Exception as e:
            logger.error(f"Falha ao alocar poltrona para '{nome_usuario}': {e}")
            salvar_screenshot(self.driver, "erro_poltrona")
            return False, str(e), None

    def preencher_dados_estudante(self, passageiro: Dict[str, any]) -> bool:
        """
        Preenche Nome, Curso e Instituição do passageiro atual.
        """
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "student-section")))

            self.driver.execute_script(
                """
                const nomeInput = document.querySelector('#name');
                const cursoInput = document.querySelector('#course');
                const instSelect = document.querySelector('#institution');

                if (nomeInput) {
                    nomeInput.value = arguments[0];
                    nomeInput.dispatchEvent(new Event('input', { bubbles: true }));
                    nomeInput.dispatchEvent(new Event('change', { bubbles: true }));
                }

                if (cursoInput) {
                    cursoInput.value = arguments[1];
                    cursoInput.dispatchEvent(new Event('input', { bubbles: true }));
                    cursoInput.dispatchEvent(new Event('change', { bubbles: true }));
                }

                if (instSelect) {
                    const alvo = arguments[2].trim().toUpperCase();
                    for (let opt of instSelect.options) {
                        if (opt.value.toUpperCase() === alvo || opt.text.toUpperCase().includes(alvo)) {
                            instSelect.value = opt.value;
                            instSelect.dispatchEvent(new Event('change', { bubbles: true }));
                            break;
                        }
                    }
                }
                """,
                passageiro["nome"],
                passageiro["curso"],
                passageiro["instituicao"],
            )

            # Aguarda a ativação do botão de confirmação
            self.wait.until(
                lambda d: d.find_element(By.ID, "confirm").is_enabled()
            )
            return True
        except Exception as e:
            logger.error(f"Falha ao preencher dados de '{passageiro.get('nome')}': {e}")
            salvar_screenshot(self.driver, "erro_preenchimento")
            return False

    def conferir_dados_antes_confirmar(
        self, data_esperada_br: str, poltrona_efetiva: int, passageiro: Dict[str, any]
    ) -> bool:
        """
        Conferência de segurança pré-confirmação.
        """
        try:
            data_atual = self.driver.find_element(By.ID, "date").get_attribute("value").strip()
            label_poltrona = self.driver.find_element(By.ID, "selected-seat").text.strip()
            nome_digitado = self.driver.find_element(By.ID, "name").get_attribute("value").strip()
            curso_digitado = self.driver.find_element(By.ID, "course").get_attribute("value").strip()
            inst_select = Select(self.driver.find_element(By.ID, "institution"))
            inst_selecionada = inst_select.first_selected_option.text.strip().upper()

            if data_atual != data_esperada_br:
                logger.error(f"Data divergente: {data_atual}")
                return False

            if str(poltrona_efetiva) not in label_poltrona:
                logger.error(f"Poltrona divergente: {label_poltrona}")
                return False

            if nome_digitado.lower() != passageiro["nome"].lower():
                logger.error(f"Nome divergente: {nome_digitado}")
                return False

            if curso_digitado.lower() != passageiro["curso"].lower():
                logger.error(f"Curso divergente: {curso_digitado}")
                return False

            if passageiro["instituicao"].upper() not in inst_selecionada:
                logger.error(f"Instituição divergente: {inst_selecionada}")
                return False

            logger.info(
                f"Conferência APROVADA: Data {data_atual} | Poltrona {poltrona_efetiva} | "
                f"{nome_digitado} ({curso_digitado} - {inst_selecionada})"
            )
            return True
        except Exception as e:
            logger.error(f"Erro na conferência: {e}")
            salvar_screenshot(self.driver, "erro_conferencia")
            return False

    def confirmar_reserva(self) -> Tuple[bool, Optional[str], str]:
        """
        Clica em 'Confirmar reserva' e captura a resposta.
        """
        try:
            confirm_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "confirm")))
            self.driver.execute_script("arguments[0].click();", confirm_btn)

            self.wait.until(
                lambda d: len(d.find_element(By.ID, "message").text.strip()) > 0
            )

            msg_el = self.driver.find_element(By.ID, "message")
            texto_msg = msg_el.text.strip()
            classe_msg = msg_el.get_attribute("class") or ""

            match_codigo = re.search(r"MU-[A-Z0-9]+", texto_msg)
            codigo_reserva = match_codigo.group(0) if match_codigo else None

            if "success" in classe_msg or "sucesso" in texto_msg.lower() or codigo_reserva:
                logger.info(f"✅ RESERVA CONFIRMADA COM SUCESSO! Código: {codigo_reserva or 'N/A'}")
                return True, codigo_reserva, texto_msg

            if "já possui uma reserva" in texto_msg.lower() or "duplicada" in texto_msg.lower():
                logger.info("Reserva já realizada previamente.")
                return True, None, "Reserva já realizada."

            logger.error(f"Erro retornado: {texto_msg}")
            salvar_screenshot(self.driver, "erro_confirmacao")
            return False, None, texto_msg
        except Exception as e:
            logger.error(f"Falha na confirmação: {e}")
            salvar_screenshot(self.driver, "erro_excecao_confirmacao")
            return False, None, str(e)

    def processar_lote_com_retomada(
        self, passageiros_concluidos: Set[str]
    ) -> Tuple[bool, Set[str]]:
        """
        Executa a reserva somente para os passageiros PENDENTES da lista PASSAGEIROS.
        Se o site ainda estiver fechado, aguarda e recarrega em loop até a abertura oficial!
        """
        data_br, data_iso, _ = self.calcular_data_viagem()
        total = len(PASSAGEIROS)
        concluidos = set(passageiros_concluidos)

        # 1. Abre a interface inicial
        if not self.abrir_site():
            return False, concluidos

        # 2. Espera ativa com refresh até as vagas abrirem
        if not self.aguardar_e_recarregar_ate_abertura(data_br, data_iso):
            return False, concluidos

        poltronas_reservadas_nesta_sessao: List[int] = []

        # 3. Itera pelos passageiros, pulando os que já tiveram sucesso
        for i, passageiro in enumerate(PASSAGEIROS, start=1):
            nome = passageiro["nome"]

            if nome in concluidos:
                logger.info(f"[{i}/{total}] '{nome}' JÁ CONCLUÍDO. Pulando para o próximo...")
                continue

            poltrona_pref = passageiro.get("poltrona_preferencial", 47)
            logger.info(f"\n[{i}/{total}] Processando passageiro pendente: '{nome}' (Denominada: {poltrona_pref})...")

            # Seleciona o ônibus 0542
            if not self.selecionar_onibus(ONIBUS_CONFIG["numero"], ONIBUS_CONFIG["motorista"]):
                logger.error(f"Falha ao selecionar ônibus para '{nome}'.")
                return False, concluidos

            # Aloca a poltrona (denominada ou mais próxima disponível)
            poltrona_ok, status_p, poltrona_escolhida = self.selecionar_poltrona(
                poltrona_pref, nome, poltronas_reservadas_nesta_sessao
            )

            if not poltrona_ok:
                logger.error(f"Não foi possível alocar poltrona para '{nome}'.")
                return False, concluidos

            if status_p == "JA_RESERVADO":
                concluidos.add(nome)
                if poltrona_escolhida:
                    poltronas_reservadas_nesta_sessao.append(poltrona_escolhida)
                continue

            # Preenche o formulário
            if not self.preencher_dados_estudante(passageiro):
                return False, concluidos

            # Confere antes de clicar
            if not self.conferir_dados_antes_confirmar(data_br, poltrona_escolhida, passageiro):
                return False, concluidos

            # Confirma a reserva
            sucesso, codigo, _ = self.confirmar_reserva()
            if sucesso:
                concluidos.add(nome)
                poltronas_reservadas_nesta_sessao.append(poltrona_escolhida)
                logger.info(f"Passageiro {i} ('{nome}') RESERVADO com êxito na poltrona {poltrona_escolhida}!")
            else:
                logger.error(f"Falha ao confirmar reserva para '{nome}'.")
                return False, concluidos

            # Se ainda houver passageiros pendentes para cadastrar, dá refresh para atualizar o mapa de poltronas e nomes
            if len(concluidos) < total and i < total:
                logger.info("Atualizando site com refresh para recarregar o mapa de poltronas e nomes em tempo real...")
                time.sleep(0.3)
                self.driver.refresh()
                self.wait.until(EC.presence_of_element_located((By.ID, "date")))
                self.wait.until(EC.presence_of_element_located((By.ID, "bus-list")))
                self.preencher_data(data_br, data_iso)

        todos_sucesso = len(concluidos) == total
        return todos_sucesso, concluidos

    def executar_fluxo_completo(self) -> bool:
        """
        Execução direta do lote inteiro do zero.
        """
        sucesso, _ = self.processar_lote_com_retomada(set())
        return sucesso
