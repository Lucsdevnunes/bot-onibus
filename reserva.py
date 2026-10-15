# ==============================================================================
# MÓDULO DE RESERVA ULTRA-RÁPIDO VIA API DIRETA (SUPABASE RPC)
# Velocidade: ~1.5s a 2.0s para todos os passageiros
# Zero dependência de cliques no DOM ou renderização lenta de navegador
# ==============================================================================
import json
import logging
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from config import BROWSER_CONFIG, ONIBUS_CONFIG, PASSAGEIROS, SITE_URL, TIMEZONE

logger = logging.getLogger("BotReserva")

SUPABASE_URL = "https://ijavkuwlcascnwnucbgm.supabase.co"
SUPABASE_KEY = "sb_publishable_CJvBm4ZD5q2uz0E8hxf81w_ZiXdHels"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def chamar_rpc(nome_funcao: str, payload: dict, timeout: float = 8.0) -> Tuple[bool, any]:
    """
    Executa uma Remote Procedure Call (RPC) diretamente no Supabase do sistema.
    """
    url = f"{SUPABASE_URL}/rest/v1/rpc/{nome_funcao}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            corpo = resp.read().decode("utf-8")
            return True, json.loads(corpo) if corpo else {}
    except urllib.error.HTTPError as e:
        erro_txt = e.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {e.code}: {erro_txt}"
    except Exception as e:
        return False, str(e)


class AutomacaoReserva:
    """
    Motor de reserva de alta performance via API direta do sistema de Maurilândia.
    Garante alocação por proximidade, espera ativa instantânea e obtenção dos códigos oficiais MU-.
    """

    def __init__(self, driver=None):
        self.driver = driver
        self.onibus_id = 1  # Ônibus 1 = Ônibus 0542 (Dheimes)

    @staticmethod
    def calcular_data_viagem() -> Tuple[str, str, datetime]:
        """
        Calcula a data alvo da viagem (SEMPRE o dia seguinte no fuso de São Paulo).
        Retorna (DD/MM/AAAA, AAAA-MM-DD, datetime_amanha).
        """
        agora = datetime.now(TIMEZONE)
        amanha = agora + timedelta(days=1)
        data_br = amanha.strftime("%d/%m/%Y")
        data_iso = amanha.strftime("%Y-%m-%d")
        return data_br, data_iso, amanha

    def consultar_poltronas_ocupadas(self, data_iso: str) -> Tuple[Set[int], Dict[int, str]]:
        """
        Consulta em tempo real quais poltronas do ônibus 0542 já estão ocupadas.
        Retorna (conjunto_de_poltronas_ocupadas, mapa_poltrona_para_nome).
        """
        sucesso, res = chamar_rpc(
            "consultar_poltronas_ocupadas_detalhes",
            {"p_data": data_iso, "p_onibus": self.onibus_id},
        )
        ocupadas: Set[int] = set()
        nomes_por_poltrona: Dict[int, str] = {}

        if sucesso and isinstance(res, list):
            for item in res:
                p_num = item.get("poltrona")
                if p_num is not None:
                    p_int = int(p_num)
                    ocupadas.add(p_int)
                    nomes_por_poltrona[p_int] = item.get("nome", "")

        return ocupadas, nomes_por_poltrona

    def verificar_cota_disponivel(self, data_iso: str) -> Tuple[bool, int, str]:
        """
        Verifica a cota de vagas para a UniRV no ônibus 0542.
        """
        sucesso, res = chamar_rpc(
            "verificar_cota_unirv",
            {"p_data": data_iso, "p_onibus": self.onibus_id},
        )
        if sucesso and isinstance(res, dict):
            liberada = res.get("liberada", True)
            restantes = res.get("restantes", 0)
            msg = res.get("mensagem", "")
            return liberada, restantes, msg
        return True, 48, ""

    def calcular_ordem_poltronas(self, poltrona_pref: int) -> List[int]:
        """
        Gera a ordem de tentativa por proximidade:
        1º: poltrona preferencial
        2º: poltronas vizinhas decrescentes
        3º: poltronas vizinhas crescentes
        """
        ordem = [poltrona_pref]
        for p in range(poltrona_pref - 1, 0, -1):
            ordem.append(p)
        for p in range(poltrona_pref + 1, 49):
            if p not in ordem:
                ordem.append(p)
        return ordem

    def aguardar_abertura_vagas(self, primeiro_passageiro: Dict[str, any], data_iso: str) -> Tuple[bool, Optional[str]]:
        """
        Espera ativa ultra-rápida (polling a cada 0.25s).
        Envia a requisição do 1º passageiro em loop até o sistema abrir.
        No milissegundo em que o sistema abre, o 1º passageiro já é reservado imediatamente!
        """
        logger.info("=" * 65)
        logger.info(f"Sincronizando com a API oficial do transporte de Maurilândia...")
        logger.info(f"Data Alvo: {data_iso} | Ônibus: 0542 (Dheimes)")
        logger.info("Aguardando liberação dos assentos no sistema...")
        logger.info("=" * 65)

        poltrona_pref = primeiro_passageiro.get("poltrona_preferencial", 47)
        tentativa_probe = 1

        while True:
            # Tenta reservar diretamente o 1º passageiro
            payload = {
                "p_data": data_iso,
                "p_nome": primeiro_passageiro["nome"],
                "p_curso": primeiro_passageiro["curso"],
                "p_instituicao": primeiro_passageiro["instituicao"],
                "p_onibus": self.onibus_id,
                "p_poltrona": poltrona_pref,
                "p_tipo_transporte": "onibus",
            }

            sucesso, res = chamar_rpc("fazer_reserva_com_cota_unirv", payload)

            if sucesso and isinstance(res, dict):
                msg = (res.get("mensagem") or "").lower()
                reserva_ok = res.get("sucesso", False)
                codigo = res.get("codigo_reserva")

                # Se o sistema abriu e realizou com sucesso
                if reserva_ok or codigo:
                    logger.info("=" * 65)
                    logger.info("🎉 [SISTEMA ABERTO!] As reservas foram liberadas com sucesso!")
                    logger.info("=" * 65)
                    return True, codigo

                # Se o aluno já possuía reserva ativa
                if "já possui uma reserva" in msg:
                    logger.info("🎉 [SISTEMA ABERTO!] Sistema aberto (aluno já possuía reserva registrada).")
                    return True, None

                # Se as vagas ainda estão fechadas/encerradas
                if "encerradas" in msg or "fechadas" in msg or "não está aberta" in msg or "liberada às" in msg:
                    if tentativa_probe % 10 == 1:
                        logger.info(f"[🔒 AGUARDANDO ABERTURA] {res.get('mensagem')}. Verificando novamente...")
                    time.sleep(0.25)
                    tentativa_probe += 1
                    continue

                # Outro erro qualquer mas o sistema já está aberto
                logger.info("🎉 [SISTEMA ABERTO!] Portas abertas no sistema.")
                return True, None

            # Falha de conexão ou HTTP
            logger.warning(f"Resposta temporária: {res}. Tentando em 0.3s...")
            time.sleep(0.3)
            tentativa_probe += 1

    def processar_lote_com_retomada(
        self, passageiros_concluidos: Set[str]
    ) -> Tuple[str, Set[str]]:
        """
        Executa as reservas dos alunos pendentes em alta velocidade via API direta.
        Retorna (status, conjunto_concluidos).
        """
        data_br, data_iso, _ = self.calcular_data_viagem()
        total = len(PASSAGEIROS)
        concluidos = set(passageiros_concluidos)
        codigos_confirmados: Dict[str, str] = {}
        poltronas_concluidas: Dict[str, int] = {}
        inicio_tempo = time.time()

        # 1. Espera ativa até abertura com a 1ª requisição
        primeiro = PASSAGEIROS[0]
        if primeiro["nome"] not in concluidos:
            aberto, codigo_p1 = self.aguardar_abertura_vagas(primeiro, data_iso)
            if not aberto:
                return "ERRO_TEMPORARIO", concluidos

            if codigo_p1:
                concluidos.add(primeiro["nome"])
                p_pref = primeiro.get("poltrona_preferencial", 47)
                poltronas_concluidas[primeiro["nome"]] = p_pref
                codigos_confirmados[primeiro["nome"]] = codigo_p1
                logger.info(
                    f"✅ [1/{total}] '{primeiro['nome']}' RESERVADO NA POLTRONA {p_pref}! Código: {codigo_p1}"
                )

        # 2. Consulta estado atual de ocupação do ônibus 0542
        ocupadas, nomes_poltronas = self.consultar_poltronas_ocupadas(data_iso)
        poltronas_reservadas_sessao: Set[int] = set(ocupadas)
        for p_num in poltronas_concluidas.values():
            poltronas_reservadas_sessao.add(p_num)

        # 3. Itera imediatamente sobre cada passageiro pendente
        for i, passageiro in enumerate(PASSAGEIROS, start=1):
            nome = passageiro["nome"]
            if nome in concluidos:
                continue

            # Verifica se o aluno já tem reserva no banco
            ja_tem = False
            for p_num, nome_dono in nomes_poltronas.items():
                if nome.lower() in nome_dono.lower():
                    concluidos.add(nome)
                    poltronas_concluidas[nome] = p_num
                    logger.info(f"[{i}/{total}] '{nome}' já possui reserva confirmada na poltrona {p_num}.")
                    ja_tem = True
                    break
            if ja_tem:
                continue

            poltrona_pref = passageiro.get("poltrona_preferencial", 47)
            ordem_poltronas = self.calcular_ordem_poltronas(poltrona_pref)

            reservado_com_sucesso = False

            # Tenta na ordem de preferência / proximidade
            for poltrona_tentativa in ordem_poltronas:
                if poltrona_tentativa in poltronas_reservadas_sessao:
                    continue

                payload = {
                    "p_data": data_iso,
                    "p_nome": nome,
                    "p_curso": passageiro["curso"],
                    "p_instituicao": passageiro["instituicao"],
                    "p_onibus": self.onibus_id,
                    "p_poltrona": poltrona_tentativa,
                    "p_tipo_transporte": "onibus",
                }

                sucesso, res = chamar_rpc("fazer_reserva_com_cota_unirv", payload)

                if sucesso and isinstance(res, dict):
                    msg = (res.get("mensagem") or "").lower()
                    codigo = res.get("codigo_reserva")
                    ok = res.get("sucesso", False)

                    if ok or codigo:
                        concluidos.add(nome)
                        poltronas_reservadas_sessao.add(poltrona_tentativa)
                        poltronas_concluidas[nome] = poltrona_tentativa
                        codigos_confirmados[nome] = codigo or "CONFIRMADO"
                        logger.info(
                            f"✅ [{i}/{total}] '{nome}' RESERVADO NA POLTRONA {poltrona_tentativa}! Código: {codigo or 'N/A'}"
                        )
                        reservado_com_sucesso = True
                        break

                    if "já possui uma reserva" in msg:
                        concluidos.add(nome)
                        logger.info(f"[{i}/{total}] '{nome}' já possui reserva ativa no sistema.")
                        reservado_com_sucesso = True
                        break

                    if "ocupada" in msg:
                        # Poltrona foi pega por outro usuário no mesmo milissegundo, tenta a próxima livre
                        poltronas_reservadas_sessao.add(poltrona_tentativa)
                        continue

                    if "esgotadas" in msg or "cota" in msg:
                        logger.warning(f"🛑 [AVISO] Vagas esgotadas para a cota no ônibus 0542: {msg}")
                        return "SEM_VAGAS", concluidos

                # Se falhou a requisição, atualiza as ocupadas e tenta a próxima
                ocupadas, _ = self.consultar_poltronas_ocupadas(data_iso)
                poltronas_reservadas_sessao.update(ocupadas)

            if not reservado_com_sucesso:
                logger.error(f"❌ Não foi possível alocar vaga livre para '{nome}'.")

        duracao_total = time.time() - inicio_tempo

        # Exibe o resumo final oficial
        logger.info("=" * 65)
        logger.info(f"⚡ PROCESSO FINALIZADO EM {duracao_total:.2f} SEGUNDOS!")
        logger.info(f"Alunos Concluídos: {len(concluidos)} de {total}")
        logger.info("=" * 65)
        for i, p in enumerate(PASSAGEIROS, 1):
            nm = p["nome"]
            polt = poltronas_concluidas.get(nm, "N/A")
            cod = codigos_confirmados.get(nm, "ATIVO")
            status_txt = "✅ CONFIRMADO" if nm in concluidos else "❌ PENDENTE"
            logger.info(f" {i}. {nm} | Poltrona: {polt} | Cód: {cod} | Status: {status_txt}")
        logger.info("=" * 65)

        # Se o driver estiver aberto (no modo não-headless no PC do usuário),
        # carrega a página com os dados para visualização bonita na tela
        if self.driver:
            try:
                logger.info("Abrindo tela do navegador com o mapa atualizado para conferência visual...")
                self.driver.get(SITE_URL)
                time.sleep(1)
                self.driver.execute_script(
                    """
                    const d = document.querySelector('#date');
                    if (d) {
                        d.value = arguments[0];
                        d.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    setTimeout(() => {
                        const buses = document.querySelectorAll('#bus-list .bus');
                        for (let b of buses) {
                            if (b.innerText.includes('0542')) {
                                b.click();
                                break;
                            }
                        }
                    }, 1000);
                    """,
                    data_br,
                )
            except Exception as e:
                logger.warning(f"Não foi possível renderizar a tela visual final: {e}")

        if len(concluidos) == total:
            return "SUCESSO_TOTAL", concluidos
        return "ERRO_TEMPORARIO", concluidos
