# 🚌 Bot de Automação — Reserva Universitária Maurilândia

Bot em Python para automação do processo de reserva de assento no sistema de transporte universitário da Prefeitura de Maurilândia – GO:
[http://localhost:3000](http://localhost:3000)

---

## 📌 Funcionalidades e Regras Implementadas

- **Navegação visual com Selenium**: Interage diretamente com os elementos existentes da interface sem alterar o sistema nem o banco de dados.
- **Cálculo automático de data**: Seleciona estritamente a **data de amanhã** relativa ao dia da execução (fuso horário `America/Sao_Paulo`).
- **Ônibus fixo**: Seleciona exclusivamente o ônibus **0542 — Dheimes** (não seleciona 0519 ou 0507).
- **Poltrona fixa**: Procura e seleciona especificamente a **poltrona 47**. Se a poltrona estiver ocupada por outro passageiro, encerra a tentativa sem selecionar outra poltrona.
- **Proteção contra duplicação (Idempotência)**: Se a poltrona 47 já constar como reservada pelo usuário ou se o sistema informar reserva ativa, registra `Reserva já realizada.` e finaliza sem duplicar.
- **Conferência rigorosa pré-envio**: Todos os campos (Data, Ônibus, Poltrona, Nome, Curso, Instituição) são verificados no DOM antes do clique no botão *Confirmar reserva*.
- **Agendamento preciso**: Fuso `America/Sao_Paulo` executando nos horários estipulados:
  - **Segunda a Quinta**: às `21:59:59`
  - **Sexta e Sábado**: *Não executa*
  - **Domingo**: às `17:59:59`
- **Logs detalhados**: Registros salvos em `logs/bot.log` e transmitidos em tempo real para o console.
- **Captura automática de screenshots**: Em qualquer falha ou impedimento, salva automaticamente uma captura de tela em `screenshots/erro_YYYY-MM-DD_HH-MM-SS.png`.

---

## 📁 Estrutura do Projeto

```
bot_reserva/
│
├── main.py              # Ponto de entrada do bot e controle de CLI
├── config.py            # Dados da reserva, horários e configurações globais
├── scheduler.py         # Agendador contínuo com precisão de segundos (America/Sao_Paulo)
├── reserva.py           # Automação das etapas do site e validações
├── browser.py           # Gerenciamento do WebDriver (Chrome/Edge) e screenshots
├── requirements.txt     # Dependências do Python
├── README.md            # Documentação completa
│
├── logs/
│   └── bot.log          # Histórico de logs de execução
│
└── screenshots/         # Capturas de tela de erros e comprovantes
```

---

## 🚀 Instalação e Requisitos

### Pré-requisitos
- Python 3.11 ou superior instalado
- Navegador Google Chrome ou Microsoft Edge instalado

### 1. Instalar as dependências

No terminal ou prompt de comando:

```bash
cd bot_reserva
pip install -r requirements.txt
```

---

## 💻 Como Executar

### 1. Modo Agendado Contínuo (Padrão)

Mantém o bot em execução contínua aguardando os horários programados para disparar a reserva:

```bash
python main.py
```

O bot exibirá no terminal o tempo restante até o próximo disparo e o fuso horário ativo.

### 2. Modo Execução Imediata / Teste (`--agora`)

Executa o fluxo da reserva imediatamente para o dia seguinte sem aguardar o agendador:

```bash
python main.py --agora
```

### 3. Modo Oculto / Segundo Plano (`--headless`)

Executa o navegador em segundo plano sem abrir janela visual:

```bash
python main.py --headless
# ou para teste imediato invisível:
python main.py --agora --headless
```

---

## ⚙️ Configurações (`config.py`)

Os dados da reserva estão centralizados em `config.py`:

```python
RESERVA_DADOS = {
    "nome": "Lucas Vinnícius Nunes Moreira de Paiva",
    "curso": "Engenharia de Software",
    "instituicao": "UNIRV",
    "onibus_numero": "0542",
    "onibus_motorista": "Dheimes",
    "poltrona": 47,
}
```

---

## 📊 Logs e Screenshots

- **Arquivo de Log**: `logs/bot.log`
- **Screenshots de Erro**: `screenshots/erro_YYYY-MM-DD_HH-MM-SS.png`
- **Comprovante de Sucesso**: `screenshots/sucesso_reserva_YYYY-MM-DD_HH-MM-SS.png`
