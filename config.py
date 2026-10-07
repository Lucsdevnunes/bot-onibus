# ==============================================================================
# CONFIGURAÇÕES DO BOT DE RESERVA UNIVERSITÁRIA
# ==============================================================================
import os
from pathlib import Path
from zoneinfo import ZoneInfo

# Diretórios do projeto
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

# Garante que os diretórios necessários existam
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Arquivo de log
LOG_FILE = LOGS_DIR / "bot.log"

# URL do site de reservas (Produção / Nuvem)
SITE_URL = os.getenv("SITE_URL", "https://reserva-universitaria-maurilandia.netlify.app/")

# Fuso horário padrão do sistema e agendamento
TIMEZONE_NAME = "America/Sao_Paulo"
TIMEZONE = ZoneInfo(TIMEZONE_NAME)

# ==============================================================================
# DADOS FIXOS DO TRANSPORTE
# ==============================================================================
ONIBUS_CONFIG = {
    "numero": "0542",
    "motorista": "Dheimes",
}

# ==============================================================================
# LISTA DE PASSAGEIROS PARA RESERVA
# ==============================================================================
PASSAGEIROS = [
    {
        "nome": "Lucas Vinnícius Nunes Moreira de Paiva",
        "curso": "Engenharia de Software",
        "instituicao": "UNIRV",
        "poltrona_preferencial": 47,
    },
    {
        "nome": "Ludmilla Maria de Oliveira Rodrigues Santos",
        "curso": "Agronomia",
        "instituicao": "UNIRV",
        "poltrona_preferencial": 39,
    },
    {
        "nome": "Cafu Baroti Xavante",
        "curso": "Enfermagem",
        "instituicao": "UNIRV",
        "poltrona_preferencial": 40,
    },
    {
        "nome": "Kawê Barbosa da Silva",
        "curso": "Engenharia Mecanica",
        "instituicao": "UNIRV",
        "poltrona_preferencial": 44,
    },
    {
        "nome": "Matheus Henrique Dantas Rodrigues",
        "curso": "Engenharia de Software",
        "instituicao": "UNIRV",
        "poltrona_preferencial": 41,
    },
    {
        "nome": "Bruna Alves Andrade",
        "curso": "Psicologia",
        "instituicao": "UNIRV",
        "poltrona_preferencial": 42,
    },
]

# ==============================================================================
# CALENDÁRIO DE EXECUÇÃO (TODOS OS DIAS ÀS 21:58:59)
# ==============================================================================
HORARIOS_EXECUCAO = {
    0: (21, 58, 59),  # Segunda-feira: 21:58:59
    1: (21, 58, 59),  # Terça-feira:   21:58:59
    2: (21, 58, 59),  # Quarta-feira:  21:58:59
    3: (21, 58, 59),  # Quinta-feira:  21:58:59
    4: (21, 58, 59),  # Sexta-feira:   21:58:59
    5: (21, 58, 59),  # Sábado:        21:58:59
    6: (21, 58, 59),  # Domingo:       21:58:59
}

# ==============================================================================
# CONFIGURAÇÕES DO NAVEGADOR
# ==============================================================================
BROWSER_CONFIG = {
    "headless": False,            # False = Abre a janela do navegador visível na tela
    "timeout_segundos": 15,       # Tempo máximo de espera explícita
    "tentativas_maximas": 3,      # Tentativas em caso de erro
    "espera_entre_tentativas": 2, # Segundos entre tentativas
    "manter_aberto": True,        # Mantém a janela aberta após a reserva para conferência visual
}
