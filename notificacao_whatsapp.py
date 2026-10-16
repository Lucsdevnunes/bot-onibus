# ==============================================================================
# MÓDULO DE NOTIFICAÇÃO NO WHATSAPP VIA GREEN-API
# Envia automaticamente o resumo oficial das reservas no grupo do WhatsApp
# Com travas rigorosas contra loops, mensagens duplicadas e envios parciais
# ==============================================================================
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

from config import LOGS_DIR, PASSAGEIROS, TIMEZONE, WHATSAPP_CONFIG

logger = logging.getLogger("BotReserva")


def formatar_mensagem_grupo(
    data_br: str,
    dia_semana_str: str,
    resultados: List[Dict[str, any]],
    tempo_execucao: float,
) -> str:
    """
    Formata o texto da mensagem com padrão visual limpo e profissional.
    """
    total = len(resultados)
    sucessos = sum(1 for r in resultados if r.get("sucesso"))

    linhas = [
        "🚌 *RESERVAS CONFIRMADAS - MAURILÂNDIA* 🚌",
        f"📅 *Viagem:* {data_br} ({dia_semana_str})",
        "🚍 *Ônibus:* 0542 — Motorista Dheimes",
        "",
        "📋 *PASSAGEIROS & POLTRONAS:*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    emojis_numeros = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    # Filtra alunos que não devem aparecer no grupo (Gabriel e Gabriele)
    ocultar = [
        nome.strip().lower()
        for nome in WHATSAPP_CONFIG.get("ocultar_do_grupo", [])
    ]

    passageiros_visiveis = [
        r for r in resultados
        if not any(oc in r.get("nome", "").lower() for oc in ocultar)
    ]

    for i, res in enumerate(passageiros_visiveis):
        nm = res.get("nome", "Aluno")
        primeiro_nome = nm.split()[0] + (" " + nm.split()[1] if len(nm.split()) > 1 else "")
        polt = res.get("poltrona", "N/A")
        cod = res.get("codigo", "N/A")
        num_icone = emojis_numeros[i] if i < len(emojis_numeros) else f"{i+1}."

        linhas.append(f"{num_icone} *{primeiro_nome}*")
        linhas.append(f"💺 Poltrona: *{polt}* | 🎟️ Cód: `{cod}`")
        linhas.append("")

    linhas.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    linhas.append(f"⚡ *Status:* {sucessos}/{total} confirmados em {tempo_execucao:.1f}s!")
    linhas.append("Tenham todos uma ótima viagem! 🎒🎓")

    return "\n".join(linhas)


def enviar_mensagem_whatsapp_grupo(
    data_br: str,
    dia_semana_str: str,
    resultados: List[Dict[str, any]],
    tempo_execucao: float,
    data_iso: Optional[str] = None,
    ignorar_trava: bool = False,
) -> bool:
    """
    Dispara a notificação oficial para o grupo configurado.
    TRAVAS RIGOROSAS:
    1. Só envia se TODOS os alunos foram confirmados com sucesso (sucesso total).
    2. Só envia UMA ÚNICA VEZ por dia (trava por arquivo de lock para data_iso).
    3. Só envia se as credenciais e configurações estiverem ativadas.
    """
    if not WHATSAPP_CONFIG.get("ativado", False):
        logger.info("Notificação por WhatsApp desativada nas configurações.")
        return False

    total_esperado = len(PASSAGEIROS)
    sucessos = sum(1 for r in resultados if r.get("sucesso"))

    # TRAVA 1: Só envia se TODOS os alunos foram confirmados com êxito
    if sucessos < total_esperado or not all(r.get("sucesso") for r in resultados):
        logger.warning(
            f"🛑 [TRAVA DE SEGURANÇA] Disparo no WhatsApp CANCELADO! "
            f"Apenas {sucessos}/{total_esperado} passageiros confirmados. "
            f"A notificação só é enviada em caso de SUCESSO TOTAL de todos os alunos."
        )
        return False

    # TRAVA 2: Lock diário para prevenir disparos duplicados ou loops
    if data_iso:
        lock_file = LOGS_DIR / f"whatsapp_enviado_{data_iso}.lock"
        if lock_file.exists() and not ignorar_trava:
            logger.warning(
                f"🔒 [TRAVA DE SEGURANÇA] A notificação no WhatsApp para {data_br} ({data_iso}) "
                f"já foi enviada anteriormente hoje! Bloqueando disparo repetido."
            )
            return False

    api_url = WHATSAPP_CONFIG.get("api_url", "https://7107.api.greenapi.com")
    id_instance = WHATSAPP_CONFIG.get("id_instance", "").strip()
    api_token = WHATSAPP_CONFIG.get("api_token", "").strip()
    chat_id = WHATSAPP_CONFIG.get("chat_id", "").strip()

    if not id_instance or not api_token or not chat_id:
        logger.warning("Credenciais da Green-API incompletas. Mensagem no WhatsApp não enviada.")
        return False

    url_envio = f"{api_url}/waInstance{id_instance}/sendMessage/{api_token}"
    texto_mensagem = formatar_mensagem_grupo(
        data_br=data_br,
        dia_semana_str=dia_semana_str,
        resultados=resultados,
        tempo_execucao=tempo_execucao,
    )

    payload = {
        "chatId": chat_id,
        "message": texto_mensagem,
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url_envio,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "BotReserva/2.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            corpo = resp.read().decode("utf-8")
            logger.info("=" * 65)
            logger.info(f"📱 Notificação enviada com sucesso no grupo do WhatsApp! Resposta: {corpo}")
            logger.info("=" * 65)

            # Grava trava diária após envio com sucesso
            if data_iso:
                try:
                    lock_file = LOGS_DIR / f"whatsapp_enviado_{data_iso}.lock"
                    lock_file.write_text(
                        f"Enviado em {datetime.now(TIMEZONE).isoformat()}\n"
                        f"Data Viagem: {data_br} ({data_iso})\n"
                        f"Tempo Execucao: {tempo_execucao:.2f}s\n",
                        encoding="utf-8",
                    )
                    logger.info(f"🔒 Trava de envio diário registrada: {lock_file.name}")
                except Exception as e_lock:
                    logger.warning(f"Não foi possível salvar arquivo de lock: {e_lock}")

            return True
    except Exception as e:
        logger.error(f"Falha ao enviar notificação no grupo do WhatsApp: {e}")
        return False
