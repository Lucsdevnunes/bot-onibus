# ==============================================================================
# BOT DE RESERVA UNIVERSITÁRIA - MAURILÂNDIA/GO
# Ponto de Entrada Principal com Continuidade e Retomada Incremental
# ==============================================================================
import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from browser import criar_driver, salvar_screenshot
from config import (
    BROWSER_CONFIG,
    LOG_FILE,
    PASSAGEIROS,
    TIMEZONE,
    atingiu_horario_limite,
)
from notificacao_whatsapp import enviar_mensagem_whatsapp_grupo
from reserva import AutomacaoReserva
from scheduler import iniciar_loop_agendamento


def configurar_logger():
    """
    Configura o logger principal para console e arquivo logs/bot.log.
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

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
) -> Tuple[str, Set[str], Optional[any], List[Dict[str, any]], float, str, str, str]:
    """
    Executa uma rodada do processo para os passageiros pendentes.
    Retorna (status, concluidos, driver, resultados, duracao, data_br, data_iso, dia_sem_str).
    """
    logger = logging.getLogger("BotReserva")
    driver = None
    status = "ERRO_TEMPORARIO"
    concluidos = set(passageiros_concluidos or set())
    inicio_execucao = datetime.now(TIMEZONE)
    resultados: List[Dict[str, any]] = []
    duracao_reserva: float = 1.1
    data_br: str = ""
    data_iso: str = ""
    dia_sem_str: str = ""

    try:
        total = len(PASSAGEIROS)
        pendentes_qtd = total - len(concluidos)
        logger.info("=" * 65)
        logger.info(
            f"INÍCIO DA TENTATIVA: {inicio_execucao.strftime('%d/%m/%Y %H:%M:%S')} "
            f"| Concluídos: {len(concluidos)}/{total} | Pendentes: {pendentes_qtd}"
        )
        logger.info("=" * 65)

        # Se headless (ex: GitHub Actions), opera 100% via API direta sem peso de navegador
        driver = None if headless else criar_driver(headless=False)
        automacao = AutomacaoReserva(driver)
        (
            status,
            concluidos,
            resultados,
            duracao_reserva,
            data_br,
            data_iso,
            dia_sem_str,
        ) = automacao.processar_lote_com_retomada(concluidos)

    except Exception as e:
        logger.error(f"Erro durante a execução: {e}", exc_info=True)
        if driver:
            salvar_screenshot(driver, "erro_critico")
        status = "ERRO_TEMPORARIO"
    finally:
        manter_aberto = BROWSER_CONFIG.get("manter_aberto", False)
        deve_manter = status in ["SUCESSO_TOTAL", "SEM_VAGAS"]

        if driver:
            if deve_manter and manter_aberto and not headless:
                logger.info("Tela do navegador mantida aberta para sua conferência visual.")
            else:
                try:
                    driver.quit()
                    logger.info("Navegador da tentativa finalizado.")
                except Exception:
                    pass

        fim_execucao = datetime.now(TIMEZONE)
        duracao = (fim_execucao - inicio_execucao).total_seconds()
        logger.info(f"Fim do processo. Status: {status} (Duração: {duracao:.1f}s)")
        logger.info("=" * 65 + "\n")

    return status, concluidos, driver, resultados, duracao_reserva, data_br, data_iso, dia_sem_str


def executar_em_loop(headless: bool = False, intervalo_segundos: float = 1.0, max_tentativas: int = 150):
    """
    Executa tentativas consecutivas em looping inteligente com memória de estado.
    REGRAS DE OURO: O loop encerra em:
      1. Todos os nomes da lista forem marcados/confirmados ("SUCESSO_TOTAL").
      2. Folga de fim de semana ("FOLGA") - sem viagens/aulas no dia seguinte.
      3. O ônibus 0542 estiver lotado e não houver mais vagas ("SEM_VAGAS").
      4. O relógio atingir o horário limite ("HORARIO_LIMITE").
      5. Limite máximo de tentativas alcançado.
    """
    logger = logging.getLogger("BotReserva")
    logger.info("=" * 65)
    logger.info(">>> MODO LOOPING INTELIGENTE ATIVADO <<<")
    logger.info("Critérios de Parada:")
    logger.info("  1. Todos os alunos marcados com Sucesso")
    logger.info("  2. Folga de fim de semana (Sexta e Sábado)")
    logger.info("  3. Ônibus 0542 Lotado / Vagas esgotadas")
    logger.info("  4. Horário limite atingido (22:30 / Domingo 18:30)")
    logger.info("=" * 65)

    passageiros_concluidos: Set[str] = set()
    total = len(PASSAGEIROS)
    tentativa = 1
    dados_sucesso_final = None

    while tentativa <= max_tentativas:
        # Checagem pré-tentativa: Horário limite
        if atingiu_horario_limite():
            logger.info("=" * 65)
            logger.info("⏰ [HORÁRIO LIMITE ATINGIDO] Encerramento por horário limite.")
            logger.info(f"Concluídos até o encerramento: {len(passageiros_concluidos)}/{total} passageiro(s).")
            logger.info("=" * 65)
            break

        logger.info(f"\n>>>> TENTATIVA #{tentativa} (Progresso: {len(passageiros_concluidos)}/{total} concluídos) <<<<")
        (
            status,
            passageiros_concluidos,
            driver,
            resultados,
            duracao,
            data_br,
            data_iso,
            dia_sem,
        ) = executar_tarefa_reserva(
            headless=headless, passageiros_concluidos=passageiros_concluidos
        )

        # 0. Folga de fim de semana
        if status == "FOLGA":
            logger.info("=" * 65)
            logger.info("ℹ️ [FOLGA DE FIM DE SEMANA] Finalizando loop. Não há viagens no sábado/domingo.")
            logger.info("=" * 65)
            break

        # 1. Condição 1: Todos os nomes marcados
        if status == "SUCESSO_TOTAL" or len(passageiros_concluidos) == total:
            logger.info("=" * 65)
            logger.info(f"🎉 SUCESSO TOTAL ATINGIDO NA TENTATIVA #{tentativa}!")
            logger.info(f"Todos os {total} passageiros foram reservados com êxito.")
            logger.info("=" * 65)
            dados_sucesso_final = (data_br, dia_sem, resultados, duracao, data_iso)
            break

        # 2. Condição 2: Não tem mais vagas (Ônibus Lotado)
        elif status == "SEM_VAGAS":
            logger.info("=" * 65)
            logger.info("🛑 [REGRA DE OURO] ENCERRAMENTO: NÃO HÁ MAIS VAGAS DISPONÍVEIS!")
            logger.info(f"Concluídos até a lotação: {len(passageiros_concluidos)}/{total} passageiro(s).")
            logger.info("=" * 65)
            break

        # 3. Condição 3: Horário limite após a tentativa
        elif atingiu_horario_limite():
            logger.info("=" * 65)
            logger.info("⏰ [HORÁRIO LIMITE ATINGIDO] Encerramento por horário limite.")
            logger.info(f"Concluídos até o encerramento: {len(passageiros_concluidos)}/{total} passageiro(s).")
            logger.info("=" * 65)
            break

        # Tentativa falhou por erro temporário: tenta novamente
        else:
            faltam = total - len(passageiros_concluidos)
            logger.warning(
                f"Tentativa #{tentativa} com pendências ({len(passageiros_concluidos)}/{total} concluídos). "
                f"Retomando em {intervalo_segundos}s a partir dos passageiros pendentes..."
            )
            tentativa += 1
            time.sleep(intervalo_segundos)

    # DISPARO OFICIAL ÚNICO NO WHATSAPP SOMENTE EM CASO DE SUCESSO TOTAL
    if dados_sucesso_final:
        d_br, d_sem, res_list, dur, d_iso = dados_sucesso_final
        logger.info("=" * 65)
        logger.info("Disparando notificação oficial única no grupo do WhatsApp...")
        logger.info("=" * 65)
        enviar_mensagem_whatsapp_grupo(
            data_br=d_br,
            dia_semana_str=d_sem,
            resultados=res_list,
            tempo_execucao=dur,
            data_iso=d_iso,
        )


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
        (
            status,
            concluidos,
            driver,
            resultados,
            duracao,
            data_br,
            data_iso,
            dia_sem,
        ) = executar_tarefa_reserva(headless=args.headless)
        if (status == "SUCESSO_TOTAL" or len(concluidos) == len(PASSAGEIROS)) and resultados:
            logger.info("=" * 65)
            logger.info("Disparando notificação oficial única no grupo do WhatsApp...")
            logger.info("=" * 65)
            enviar_mensagem_whatsapp_grupo(
                data_br=data_br,
                dia_semana_str=dia_sem,
                resultados=resultados,
                tempo_execucao=duracao,
                data_iso=data_iso,
            )
    else:
        logger.info("Modo agendador contínuo ativado.")
        iniciar_loop_agendamento(lambda: executar_tarefa_reserva(headless=args.headless)[0])


if __name__ == "__main__":
    main()
