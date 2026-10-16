# ==============================================================================
# MÓDULO DE NOTIFICAÇÃO NO WHATSAPP VIA GREEN-API
# Envia automaticamente o resumo oficial das reservas no grupo do WhatsApp
# ==============================================================================
import json
import logging
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from config import WHATSAPP_CONFIG

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

    for i, res in enumerate(resultados):
        nm = res.get("nome", "Aluno")
        primeiro_nome = nm.split()[0] + (" " + nm.split()[1] if len(nm.split()) > 1 else "")
        polt = res.get("poltrona", "N/A")
        cod = res.get("codigo", "N/A")
        num_icone = emojis_numeros[i] if i < len(emojis_numeros) else f"{i+1}."

        linhas.append(f"{num_icone} *{primeiro_nome}*")
        linhas.append(f"   💺 Poltrona: *{polt}* | 🎟️ Cód: `{cod}`")
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
) -> bool:
    """
    Dispara a notificação oficial para o grupo configurado.
    """
    if not WHATSAPP_CONFIG.get("ativado", False):
        logger.info("Notificação por WhatsApp desativada nas configurações.")
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
            return True
    except Exception as e:
        logger.error(f"Falha ao enviar notificação no grupo do WhatsApp: {e}")
        return False
