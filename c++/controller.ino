#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <FastLED.h>
#include <GFButton.h>

#define ENC_CLK 2
#define ENC_DT 3
#define ENC_SW 4

#define NUM_LEDS 12
#define DATA_PIN 7

LiquidCrystal_I2C lcd(0x27, 20, 4);

byte charSeta[8] = {
  0b00000, 
  0b01000, 
  0b01100, 
  0b01110,
  0b01100, 
  0b01000, 
  0b00000, 
  0b00000
};

byte charCheck[8] = {
  0b00000, 
  0b00001, 
  0b00011, 
  0b10110,
  0b11100, 
  0b01000, 
  0b00000, 
  0b00000
};

enum Estado {
  MENU_PRINCIPAL,
  EDITANDO_INSTRUMENTO,
  EDITANDO_BPM,
  EDITANDO_ESTILO
};

Estado estadoAtual = MENU_PRINCIPAL;

const int NUM_ITENS_MENU = 3;
const char* itensMenu[NUM_ITENS_MENU] = {"BPM", "Estilo", "Instrumento"};
int cursorMenu = 0;

const int NUM_INSTRUMENTOS = 5;
const char* listaInstrumentos[NUM_INSTRUMENTOS] = {
  "Orgao", "Flauta", "Guitarra", "Bateria", "Piano"
};
int instrumentoAtual = 0;
int cursorInstrumento = 0;

int valorBPM = 100;

const int NUM_ESTILOS = 4;
const char* listaEstilos[NUM_ESTILOS] = {
  "Rock", "Jazz", "Samba", "Escolha da IA"
};
int estiloAtual = 0;
int cursorEstilo = 0;

int ultimoEstadoCLK;
bool botaoPressionado = false;
unsigned long tempoUltimoBotao = 0;
const unsigned long DEBOUNCE_MS = 250;
bool telaModificada = true;


GFButton tecla1(A8);
GFButton tecla2(A15);
GFButton tecla3(A0);
GFButton tecla4(A2);
GFButton tecla5(A3);
GFButton tecla6(A6);
GFButton tecla7(A7);

GFButton botao_play_pause(A11);
GFButton botao_gravacao(A13);

bool estado_play_pause = false;
bool estado_gravacao = false;

String notas[] = {"DO", "RE", "MI", "FA", "SOL", "LA", "SI"};

int gravacao[300];
int total_de_notas = 0;

unsigned long tempos[300];
unsigned long pausas[300];
unsigned long tempo_inicio[7] = {0, 0, 0, 0, 0, 0, 0};
unsigned long tempo_ultimo_release = 0;
unsigned long tempo_inicio_gravacao = 0;
int posicao_nota[7] = {-1, -1, -1, -1, -1, -1, -1};

CRGB leds[NUM_LEDS];


//  FUNÇÕES DAS TECLAS

void marca_nota(int nota) {
  if (estado_gravacao && total_de_notas < 300) {
    gravacao[total_de_notas] = nota;
    posicao_nota[nota] = total_de_notas;
    total_de_notas++;
  }
}

void tecla_pressed(int i) {
  leds[i] = CRGB(255, 0, 0);
  FastLED.show();
  Serial.println("{\"nota\": \"" + notas[i] + "\", \"ativa\": true}");
  if (estado_gravacao) {
    pausas[total_de_notas] = millis() - tempo_inicio_gravacao;
    tempo_inicio[i] = millis();
  }
  marca_nota(i);
}

void tecla_released(int i) {
  leds[i] = CRGB(0, 0, 0);
  FastLED.show();
  Serial.println("{\"nota\": \"" + notas[i] + "\", \"ativa\": false}");
  if (estado_gravacao && posicao_nota[i] >= 0) {
    tempos[posicao_nota[i]] = millis() - tempo_inicio[i];
    posicao_nota[i] = -1;
    tempo_ultimo_release = millis();
  }
}

void whenPressed1() { tecla_pressed(0); }
void whenPressed2() { tecla_pressed(1); }
void whenPressed3() { tecla_pressed(2); }
void whenPressed4() { tecla_pressed(3); }
void whenPressed5() { tecla_pressed(4); }
void whenPressed6() { tecla_pressed(5); }
void whenPressed7() { tecla_pressed(6); }

void whenReleased1() { tecla_released(0); }
void whenReleased2() { tecla_released(1); }
void whenReleased3() { tecla_released(2); }
void whenReleased4() { tecla_released(3); }
void whenReleased5() { tecla_released(4); }
void whenReleased6() { tecla_released(5); }
void whenReleased7() { tecla_released(6); }

void whenPressedPlayPause() {
  estado_play_pause = !estado_play_pause;
  leds[7] = estado_play_pause ? CRGB(255, 0, 0) : CRGB(0, 0, 0);
  FastLED.show();

  if (estado_play_pause) {
    Serial.print("{\"notas\":[");
    for (int i = 0; i < total_de_notas; i++) {
      Serial.print("{\"nota\":\"");
      Serial.print(notas[gravacao[i]]);
      Serial.print("\",\"inicio\":");
      Serial.print(pausas[i]);
      Serial.print(",\"duracao\":");
      Serial.print(tempos[i]);
      Serial.print("}");
      if (i < total_de_notas - 1) Serial.print(",");
    }
    Serial.println("]}");

    unsigned long duracao_total = 0;
    for (int i = 0; i < total_de_notas; i++) {
      unsigned long fim = pausas[i] + tempos[i];
      if (fim > duracao_total) duracao_total = fim;
    }

    unsigned long inicio_replay = millis();
    while (true) {
      unsigned long t = millis() - inicio_replay;
      if (t > duracao_total) break;
      for (int i = 0; i < total_de_notas; i++) {
        if (t >= pausas[i] && t < pausas[i] + tempos[i]) {
          leds[gravacao[i]] = CRGB(0, 0, 255);
        } else {
          leds[gravacao[i]] = CRGB(0, 0, 0);
        }
      }
      FastLED.show();
      delay(10);
    }
    FastLED.clear();
    FastLED.show();
  }
}

void whenPressedGravacao() {
  if (!estado_gravacao) {
    total_de_notas = 0;
    tempo_inicio_gravacao = millis();
    tempo_ultimo_release = millis();
  }
  estado_gravacao = !estado_gravacao;
  leds[8] = estado_gravacao ? CRGB(255, 0, 0) : CRGB(0, 0, 0);
  FastLED.show();
}


//  FUNÇÕES DO LCD / ENCODER

void imprimirEstadoSerial() {
  Serial.print("{");
  Serial.print("\"instrumento\":\"");
  Serial.print(listaInstrumentos[instrumentoAtual]);
  Serial.print("\"");
  Serial.print(",\"bpm\":");
  Serial.print(valorBPM);
  Serial.print(",\"estilo\":\"");
  Serial.print(listaEstilos[estiloAtual]);
  Serial.print("\"");
  Serial.println("}");
}

void lerEncoder() {
  int estadoAtualCLK = digitalRead(ENC_CLK);
  if (estadoAtualCLK != ultimoEstadoCLK && estadoAtualCLK == LOW) {
    int direcao = (digitalRead(ENC_DT) != estadoAtualCLK) ? 1 : -1;
    switch (estadoAtual) {
      case MENU_PRINCIPAL:
        cursorMenu = constrain(cursorMenu + direcao, 0, NUM_ITENS_MENU - 1);
        break;
      case EDITANDO_INSTRUMENTO:
        cursorInstrumento = constrain(cursorInstrumento + direcao, 0, NUM_INSTRUMENTOS - 1);
        break;
      case EDITANDO_BPM:
        valorBPM = constrain(valorBPM + direcao, 20, 300);
        break;
      case EDITANDO_ESTILO:
        cursorEstilo = constrain(cursorEstilo + direcao, 0, NUM_ESTILOS - 1);
        break;
    }
    telaModificada = true;
  }
  ultimoEstadoCLK = estadoAtualCLK;
}

void lerBotao() {
  bool leitura = (digitalRead(ENC_SW) == LOW);
  if (leitura && !botaoPressionado && (millis() - tempoUltimoBotao > DEBOUNCE_MS)) {
    botaoPressionado = true;
    tempoUltimoBotao = millis();

    switch (estadoAtual) {
      case MENU_PRINCIPAL:
        if (cursorMenu == 0) { estadoAtual = EDITANDO_BPM; }
        else if (cursorMenu == 1) { estadoAtual = EDITANDO_ESTILO; cursorEstilo = estiloAtual; }
        else if (cursorMenu == 2) { estadoAtual = EDITANDO_INSTRUMENTO; cursorInstrumento = instrumentoAtual; }
        break;
      case EDITANDO_INSTRUMENTO:
        instrumentoAtual = cursorInstrumento;
        estadoAtual = MENU_PRINCIPAL;
        imprimirEstadoSerial();
        break;
      case EDITANDO_BPM:
        estadoAtual = MENU_PRINCIPAL;
        imprimirEstadoSerial();
        break;
      case EDITANDO_ESTILO:
        estiloAtual = cursorEstilo;
        estadoAtual = MENU_PRINCIPAL;
        imprimirEstadoSerial();
        break;
    }
    telaModificada = true;
  }
  if (!leitura) botaoPressionado = false;
}

void desenharMenuPrincipal() {
  lcd.setCursor(0, 0);
  lcd.print("- MENU -   - ATUAL -");
  for (int i = 0; i < NUM_ITENS_MENU; i++) {
    lcd.setCursor(0, i + 1);
    if (i == cursorMenu) lcd.write(byte(0));
    else lcd.print(" ");
    lcd.print(itensMenu[i]);

    lcd.setCursor(13, i + 1);
    if (i == 0) {
      lcd.print("["); lcd.print(valorBPM); lcd.print("]");
    } else if (i == 1) {
      String est = listaEstilos[estiloAtual];
      if (est.length() > 5) est = est.substring(0, 5);
      lcd.print("["); lcd.print(est); lcd.print("]");
    } else {
      String inst = listaInstrumentos[instrumentoAtual];
      if (inst.length() > 5) inst = inst.substring(0, 5);
      lcd.print("["); lcd.print(inst); lcd.print("]");
    }
  }
}

void desenharSeletorInstrumento() {
  lcd.setCursor(0, 0);
  lcd.print("-> Instrumento");
  int inicioScroll = (cursorInstrumento >= 3) ? cursorInstrumento - 2 : 0;
  for (int v = 0; v < 3; v++) {
    int idx = inicioScroll + v;
    if (idx >= NUM_INSTRUMENTOS) break;
    int linha = v + 1;
    lcd.setCursor(0, linha);
    if (idx == cursorInstrumento) {
      lcd.print(" ");
      lcd.write(byte(0));
      lcd.print(" ");
    } else {
      lcd.print("   ");
    }
    lcd.print(listaInstrumentos[idx]);
    if (idx == instrumentoAtual) {
      lcd.setCursor(18, linha);
      lcd.write(byte(1));
    }
  }
}

void desenharEditorBPM() {
  lcd.setCursor(0, 0);
  lcd.print("-> BPM");
  lcd.setCursor(2, 1);
  lcd.print("Velocidade: [");
  lcd.print(valorBPM);
  lcd.print("]");
  lcd.setCursor(0, 2);
  lcd.print("Gire para alterar");
  lcd.setCursor(0, 3);
  lcd.print("Clique para salvar");
}

void desenharSeletorEstilo() {
  lcd.setCursor(0, 0);
  lcd.print("-> Estilo");
  int inicioScroll = (cursorEstilo >= 3) ? cursorEstilo - 2 : 0;
  for (int v = 0; v < 3; v++) {
    int idx = inicioScroll + v;
    if (idx >= NUM_ESTILOS) break;
    int linha = v + 1;
    lcd.setCursor(0, linha);
    if (idx == cursorEstilo) {
      lcd.print(" ");
      lcd.write(byte(0));
      lcd.print(" ");
    } else {
      lcd.print("   ");
    }
    lcd.print(listaEstilos[idx]);
    if (idx == estiloAtual) {
      lcd.setCursor(18, linha);
      lcd.write(byte(1));
    }
  }
}

void desenharTela() {
  lcd.clear();
  switch (estadoAtual) {
    case MENU_PRINCIPAL: desenharMenuPrincipal(); break;
    case EDITANDO_INSTRUMENTO: desenharSeletorInstrumento(); break;
    case EDITANDO_BPM: desenharEditorBPM(); break;
    case EDITANDO_ESTILO: desenharSeletorEstilo(); break;
  }
}


//  SETUP & LOOP


void setup() {
  Serial.begin(9600);

  // Encoder
  pinMode(ENC_CLK, INPUT);
  pinMode(ENC_DT,  INPUT);
  pinMode(ENC_SW,  INPUT_PULLUP);
  ultimoEstadoCLK = digitalRead(ENC_CLK);

  // LCD
  lcd.init();
  lcd.backlight();
  lcd.createChar(0, charSeta);
  lcd.createChar(1, charCheck);
  lcd.clear();
  telaModificada = true;
  imprimirEstadoSerial();

  // LEDs
  FastLED.addLeds<WS2812, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.clear();
  FastLED.show();

  // Teclas
  tecla1.setPressHandler(whenPressed1);
  tecla1.setReleaseHandler(whenReleased1);
  tecla2.setPressHandler(whenPressed2);
  tecla2.setReleaseHandler(whenReleased2);
  tecla3.setPressHandler(whenPressed3);
  tecla3.setReleaseHandler(whenReleased3);
  tecla4.setPressHandler(whenPressed4);
  tecla4.setReleaseHandler(whenReleased4);
  tecla5.setPressHandler(whenPressed5);
  tecla5.setReleaseHandler(whenReleased5);
  tecla6.setPressHandler(whenPressed6);
  tecla6.setReleaseHandler(whenReleased6);
  tecla7.setPressHandler(whenPressed7);
  tecla7.setReleaseHandler(whenReleased7);

  botao_play_pause.setPressHandler(whenPressedPlayPause);
  botao_gravacao.setPressHandler(whenPressedGravacao);
}

void loop() {
  // Encoder + LCD
  lerEncoder();
  lerBotao();
  if (telaModificada) {
    desenharTela();
    telaModificada = false;
  }

  // Teclas
  tecla1.process();
  tecla2.process();
  tecla3.process();
  tecla4.process();
  tecla5.process();
  tecla6.process();
  tecla7.process();

  botao_play_pause.process();
  botao_gravacao.process();
}
