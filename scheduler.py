# ==============================================================================
# MÓDULO DE AGENDAMENTO (SCHEDULER COM PRÉ-AQUECIMENTO DE ALTA VELOCIDADE)
# ==============================================================================
import logging
import time
from datetime import datetime, timedelta
from typing import Callable, Optional, Tuple

from config import BROWSER_CONFIG, HORARIOS_EXECUCAO, TIMEZONE

logger = logging.getLogger("BotReserva")


def obter_horario_atual() -> datetime:
    """
    Retorna o datetime atual no fuso horário America/Sao_Paulo.
    """
    return datetime.now(TIMEZONE)


def calcular_proximo_disparo(referencia: Optional[datetime] = None) -> Tuple[datetime, int]:
    """
    Calcula o próximo horário de execução no calendário:
    - Segunda a Quinta: 21:59:59
    - Domingo: 17:59:59
    - Sexta e Sábado: Não executa
    """
    agora = referencia or obter_horario_atual()

    for offset_dias in range(14):
        candidato_data = agora + timedelta(days=offset_dias)
        dia_semana = candidato_data.weekday()

        horario = HORARIOS_EXECUCAO.get(dia_semana)
        if horario is None:
            continue

        hora, minuto, segundo = horario
        candidato_disparo = candidato_data.replace(
            hour=hora, minute=minuto, second=segundo, microsecond=0
        )

        if candidato_disparo > agora:
            return candidato_disparo, dia_semana

    raise RuntimeError("Não foi possível calcular o próximo horário.")


def formatar_tempo_restante(segundos_totais: float) -> str:
    segundos = int(segundos_totais)
    dias, resto = divmod(segundos, 86400)
    horas, resto = divmod(resto, 3600)
    minutos, segs = divmod(resto, 60)

    partes = []
    if dias > 0:
        partes.append(f"{dias}d")
    if horas > 0 or dias > 0:
        partes.append(f"{horas}h")
    if minutos > 0 or horas > 0 or dias > 0:
        partes.append(f"{minutos}m")
    partes.append(f"{segs}s")

    return " ".join(partes)


def iniciar_loop_agendamento(funcao_execucao: Callable[[], bool]):
    """
    Loop de agendamento contínuo com precisão de milissegundos e pré-aquecimento.
    """
    logger.info("Agendador automático ativado em alta performance (Modo Headless).")
    logger.info("Fuso: America/Sao_Paulo | Seg a Qui (21:59:59) | Domingo (17:59:59)")

    nomes_dias = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]

    while True:
        try:
            agora = obter_horario_atual()
            proximo_disparo, dia_semana = calcular_proximo_disparo(agora)
            diferenca = (proximo_disparo - agora).total_seconds()

            logger.info(
                f"Próxima execução: {proximo_disparo.strftime('%d/%m/%Y às %H:%M:%S')} "
                f"({nomes_dias[dia_semana]}) — Faltam {formatar_tempo_restante(diferenca)}"
            )

            # Aguarda com polling adaptativo
            while True:
                agora = obter_horario_atual()
                restante = (proximo_disparo - agora).total_seconds()

                if restante <= 0:
                    break

                if restante > 300:
                    time.sleep(30)
                elif restante > 30:
                    time.sleep(5)
                elif restante > 2:
                    time.sleep(0.5)
                else:
                    time.sleep(0.01)  # Precisão de centésimos de segundo

            logger.info("=" * 65)
            logger.info(f"DISPARO EM TEMPO REAL: {obter_horario_atual().strftime('%d/%m/%Y %H:%M:%S.%f')[:-3]}")
            logger.info("=" * 65)

            sucesso = funcao_execucao()
            logger.info(f"Resultado da execução: {'SUCESSO' if sucesso else 'FALHA'}")
            logger.info("Aguardando próximo ciclo...\n")

            time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Agendador encerrado pelo usuário.")
            break
        except Exception as e:
            logger.error(f"Erro no loop do agendador: {e}", exc_info=True)
            time.sleep(5)
