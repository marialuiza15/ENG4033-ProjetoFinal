# SmartBeat - Brinquedo musical com IA

Projeto final de Microcontroladores (ENG4033): um brinquedo musical interativo que permite tocar notas em um controlador caseiro, gravar uma pequena melodia e usar IA para transformar essa ideia inicial em uma sequência musical mais completa.

O sistema junta três partes:

- um controlador físico com Arduino, teclas, LCD, potenciômetro/encoder, botões e fita de LED;
- um programa em Python que recebe eventos pela serial, toca o áudio com FluidSynth e mantém uma batida em loop;
- um módulo de IA que recebe a melodia gravada em JSON e devolve uma nova sequência musical.

## Visão geral

O fluxo principal é:

1. O usuário escolhe BPM, estilo e instrumento no LCD do controlador.
2. As teclas musicais enviam eventos pela serial em tempo real.
3. O Python lê esses eventos e toca as notas usando uma SoundFont.
4. Ao iniciar uma gravação, o Arduino salva nota, início e duração.
5. Ao apertar play, o Arduino envia a sequência gravada em JSON.
6. O Python converte as notas para MIDI, chama a IA e toca a música gerada.

## Estrutura do projeto

```text
.
├── c++/
│   └── controller.ino          # Firmware principal do controlador
├── py/
│   ├── ia/
│   │   ├── audioLeitura.py     # Integração com IA local ou Gemini
│   │   └── teste_ia.py         # Teste isolado da geração por IA
│   ├── music_player/
│   │   ├── main.py             # Programa principal de áudio + serial
│   │   ├── main2.py            # Versão anterior/alternativa
│   │   └── arquivos_musicais/
│   │       ├── batidas.json
│   │       ├── musica_completa.json
│   │       ├── musica_gerada.json
│   │       ├── notas.json
│   │       └── FluidR3_GM.sf2
│   └── dashboard/
│       ├── smartbeat_dashboard.py
│       └── smartbeat_tkinter.py
└── README.md
```

## Hardware

O firmware principal está em `c++/controller.ino`.

Componentes usados:

- Arduino compatível com múltiplas entradas analógicas, como Arduino Mega;
- LCD I2C 20x4 no endereço `0x27`;
- fita de LED WS2812 com 12 LEDs;
- 7 botões para notas musicais;
- botão verde de play/pause;
- botão vermelho de gravação;
- potenciômetro ou controle analógico para navegar/editar o menu;
- botão do encoder para alternar entre navegação e edição.

Pinagem usada no firmware:

| Função | Pino |
| --- | --- |
| Botão do encoder | `4` |
| Potenciômetro/menu | `A5` |
| Dados da fita LED | `6` |
| Nota DO | `A15` |
| Nota RE | `A8` |
| Nota MI | `A7` |
| Nota FA | `A6` |
| Nota SOL | `A3` |
| Nota LA | `A2` |
| Nota SI | `A0` |
| Play/pause | `A11` |
| Gravação | `A13` |

Bibliotecas Arduino:

- `Wire`
- `LiquidCrystal_I2C`
- `FastLED`
- `GFButton`

## Firmware

Abra `c++/controller.ino` na Arduino IDE e grave na placa.

O menu do LCD possui três campos:

- `BPM`: varia de 20 a 300;
- `Estilo`: `Rock`, `Jazz`, `Samba` ou `Opcao IA`;
- `Inst.`: `Orgao`, `Flauta`, `Guitarra`, `Bateria` ou `Piano`.

O Arduino envia mensagens JSON pela serial em `9600 baud`.

Exemplos de mensagens:

```json
{"instrumento":"Orgao","bpm":100,"estilo":"Rock"}
```

```json
{"nota":"DO","ativa":true}
```

```json
{"gravando":true}
```

```json
{
  "notas": [
    {"nota": "DO", "inicio": 0, "duracao": 500},
    {"nota": "MI", "inicio": 500, "duracao": 500}
  ]
}
```

## Python e áudio

O programa principal é `py/music_player/main.py`.

Ele faz:

- listagem das portas seriais disponíveis;
- leitura dos JSONs enviados pelo Arduino;
- execução de notas ao vivo;
- execução de batidas em loop conforme o estilo escolhido;
- conversão das notas `DO`, `RE`, `MI`, `FA`, `SOL`, `LA`, `SI` para valores MIDI;
- chamada do módulo de IA para melhorar a melodia;
- reprodução da música gerada com FluidSynth.

### Dependências

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as bibliotecas Python usadas pelo projeto:

```powershell
pip install pyserial pyfluidsynth requests streamlit
```

Também é necessário ter o FluidSynth funcionando. O projeto já inclui uma pasta de FluidSynth para Windows dentro de `py/music_player/arquivos_musicais/`, e o `main.py` tenta localizar automaticamente o diretório `bin`.

### Rodar com Arduino

```powershell
python py\music_player\main.py
```

O programa vai listar as portas seriais disponíveis. Digite a porta do Arduino, por exemplo:

```text
COM3
```

### Rodar sem Arduino

Ao executar:

```powershell
python py\music_player\main.py
```

pressione `ENTER` sem digitar uma porta. O programa entra em modo de teste, toca uma sequência simples e executa a lógica principal sem depender do controlador físico.

## IA

O módulo de IA está em `py/ia/audioLeitura.py`.

Por padrão, a função usada pelo player é `gerar_sequencia_musical`, que chama uma API local compatível com OpenAI em:

```text
http://localhost:1234/v1/chat/completions
```

Modelo configurado no código:

```text
google/genma-4-e4b
```

Esse endpoint pode ser fornecido por uma ferramenta local de LLM, desde que exponha a rota `/v1/chat/completions`.

Existe também uma função alternativa, `gerar_sequencia_musical_gemini`, preparada para usar Gemini com a variável `GEMINI_API_KEY` no arquivo `.env`, mas ela não é chamada pelo `main.py` atualmente.

Formato esperado da resposta da IA:

```json
{
  "sequencia": [
    {"nota": 60, "inicio": 0, "duracao": 500}
  ],
  "instrumento": "Orgao",
  "bpm": 120,
  "estilo": "Rock"
}
```

## Batidas e arquivos musicais

As batidas ficam em:

```text
py/music_player/arquivos_musicais/batidas.json
```

Cada estilo possui:

- `duracao_padrao`: duração do ciclo da batida em milissegundos;
- `eventos`: lista de notas MIDI de bateria com início, duração e instrumento.

Exemplo simplificado:

```json
{
  "Rock": {
    "duracao_padrao": 2000,
    "eventos": [
      {"nota": 36, "inicio": 0, "duracao": 100, "instrumento": "Bateria"}
    ]
  }
}
```

## Dashboard

Há dois protótipos de dashboard em `py/dashboard/`:

- `smartbeat_dashboard.py`: interface Streamlit;
- `smartbeat_tkinter.py`: interface Tkinter.

Para rodar o dashboard Streamlit:

```powershell
streamlit run py\dashboard\smartbeat_dashboard.py
```

O dashboard ainda funciona como tela de configuração/protótipo visual. A integração principal do projeto está no controlador Arduino e em `py/music_player/main.py`.

## Como demonstrar

1. Grave `c++/controller.ino` no Arduino.
2. Conecte o controlador ao computador.
3. Ative o ambiente Python.
4. Rode `python py\music_player\main.py`.
5. Escolha a porta serial do Arduino.
6. Use o menu físico para selecionar BPM, estilo e instrumento.
7. Toque as teclas para ouvir notas em tempo real.
8. Aperte o botão de gravação para iniciar/parar a captura.
9. Aperte play para enviar a melodia gravada.
10. O Python envia a sequência para a IA e toca a música melhorada.

## Observações

- A comunicação entre Arduino e Python depende de JSON válido em uma linha por mensagem.
- O limite de gravação no Arduino é de `300` notas.
- O player usa nomes de instrumento exatamente como enviados pelo firmware: `Piano`, `Guitarra`, `Orgao`, `Flauta` e `Bateria`.
- Os estilos do firmware precisam existir em `batidas.json`.
- A IA local precisa estar rodando antes de usar a geração automática.
- Se a IA estiver indisponível, o modo de teste sem Arduino ainda valida parte do fluxo de áudio, mas a chamada de geração pode falhar.

## Autores

Projeto desenvolvido para a disciplina ENG4033 - Microcontroladores.
