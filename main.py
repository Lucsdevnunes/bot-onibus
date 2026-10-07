# ==============================================================================
# BOT DE RESERVA UNIVERSITÁRIA - MAURILÂNDIA/GO
# Ponto de Entrada Principal com Continuidade e Retomada Incremental
# ==============================================================================
import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Optional, Set, Tuple

from browser import criar_driver, salvar_screenshot
from config import BROWSER_CONFIG, LOG_FILE, PASSAGEIROS, TIMEZONE
from reserva import AutomacaoReserva
from scheduler import iniciar_loop_agendamento


def configurar_logger():
    """
    Configura o logger principal para console e arquivo logs/bot.log.
    """
    logger = logging.getLogger("BotReserva")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formato = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formato)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formato)
    logger.addHandler(console_handler)

    return logger


def executar_tarefa_reserva(
    headless: bool = False, passageiros_concluidos: Optional[Set[str]] = None
) -> Tuple[bool, Set[str], Optional[any]]:
    """
    Executa uma rodada do processo para os passageiros pendentes.
    Retorna (todos_sucesso, conjunto_concluidos, driver).
    """
    logger = logging.getLogger("BotReserva")
    driver = None
    sucesso = False
    concluidos = set(passageiros_concluidos or set())
    inicio_execucao = datetime.now(TIMEZONE)

    try:
        total = len(PASSAGEIROS)
        pendentes_qtd = total - len(concluidos)
        logger.info("=" * 65)
        logger.info(
            f"INÍCIO DA TENTATIVA: {inicio_execucao.strftime('%d/%m/%Y %H:%M:%S')} "
            f"| Concluídos: {len(concluidos)}/{total} | Pendentes: {pendentes_qtd}"
        )
        logger.info("=" * 65)

        driver = criar_driver(headless=headless)
        automacao = AutomacaoReserva(driver)
        sucesso, concluidos = automacao.processar_lote_com_retomada(concluidos)

    except Exception as e:
        logger.error(f"Erro durante a execução: {e}", exc_info=True)
        if driver:
            salvar_screenshot(driver, "erro_critico")
        sucesso = False
    finally:
        manter_aberto = BROWSER_CONFIG.get("manter_aberto", False)
        # Se deu sucesso completo e manter_aberto=True, NÃO fecha o navegador
        if driver:
            if sucesso and manter_aberto and not headless:
                logger.info("Tela do navegador mantida aberta para sua conferência visual.")
            else:
                try:
                    driver.quit()
                    logger.info("Navegador da tentativa finalizado.")
                except Exception:
                    pass

        fim_execucao = datetime.now(TIMEZONE)
        duracao = (fim_execucao - inicio_execucao).total_seconds()
        status_str = "SUCESSO" if sucesso else "NÃO CONCLUÍDA / COM ERROS"
        logger.info(f"Fim do processo. Status: {status_str} (Duração: {duracao:.1f}s)")
        logger.info("=" * 65 + "\n")

    return sucesso, concluidos, driver


def executar_em_loop(headless: bool = False, intervalo_segundos: float = 1.0):
    """
    Executa tentativas consecutivas em looping inteligente com memória de estado.
    Se o aluno 1 der certo e o 2 falhar, a próxima tentativa recomeça do 2 em diante!
    O looping só encerra quando TODOS os passageiros estiverem com Status: SUCESSO.
    """
    logger = logging.getLogger("BotReserva")
    logger.info("=" * 65)
    logger.info(">>> MODO LOOPING INTELIGENTE ATIVADO (COM RETOMADA INCREMENTAL) <<<")
    logger.info("O bot só vai parar quando TODOS os passageiros forem confirmados com SUCESSO!")
    logger.info("=" * 65)

    passageiros_concluidos: Set[str] = set()
    total = len(PASSAGEIROS)
    tentativa = 1

    while True:
        logger.info(f"\n>>>> TENTATIVA #{tentativa} (Progresso: {len(passageiros_concluidos)}/{total} concluídos) <<<<")
        sucesso, passageiros_concluidos, driver = executar_tarefa_reserva(
            headless=headless, passageiros_concluidos=passageiros_concluidos
        )

        if sucesso and len(passageiros_concluidos) == total:
            logger.info("=" * 65)
            logger.info(f"🎉 SUCESSO TOTAL ATINGIDO NA TENTATIVA #{tentativa}!")
            logger.info(f"Todos os {total} passageiros foram reservados com êxito.")
            logger.info("A tela permanecerá aberta no navegador para sua conferência.")
            logger.info("=" * 65)
            break
        else:
            faltam = total - len(passageiros_concluidos)
            logger.warning(
                f"Tentativa #{tentativa} finalizada. Concluídos: {len(passageiros_concluidos)}/{total}. "
                f"Faltam {faltam} passageiro(s). Retomando em {intervalo_segundos}s a partir dos pendentes..."
            )
            tentativa += 1
            time.sleep(intervalo_segundos)


def main():
    """
    Função de entrada da linha de comando.
    """
    parser = argparse.ArgumentParser(
        description="Bot de Automação para Reserva de Transporte Universitário (Maurilândia/GO)"
    )
    parser.add_argument(
        "--agora",
        "--test",
        action="store_true",
        help="Executa o lote da reserva imediatamente para o dia seguinte."
    )
    parser.add_argument(
        "--loop",
        "--looping",
        action="store_true",
        help="Executa em repetição contínua (looping) com retomada incremental até obter SUCESSO total."
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Executa o navegador em modo oculto (headless)."
    )

    args = parser.parse_args()
    logger = configurar_logger()

    logger.info("==================================================================")
    logger.info("BOT DE RESERVA UNIVERSITÁRIA - MAURILÂNDIA/GO")
    logger.info("==================================================================")

    if args.loop:
        executar_em_loop(headless=args.headless)
    elif args.agora:
        logger.info("Modo de execução imediata ativado (--agora).")
        executar_tarefa_reserva(headless=args.headless)
    else:
        logger.info("Modo agendador contínuo ativado.")
        iniciar_loop_agendamento(lambda: executar_tarefa_reserva(headless=args.headless)[0])


if __name__ == "__main__":
    main()
