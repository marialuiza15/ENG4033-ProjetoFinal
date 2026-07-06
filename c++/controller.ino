#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <FastLED.h> //pra fita de led
#include <GFButton.h>

// pinos do encoder
#define ENC_CLK  2   
#define ENC_DT   3  
#define ENC_SW   4

#define NUM_LEDS  12 //numero de leds na fita
#define DATA_PIN  7 //pino da fita led
#define MAX_NOTAS 300 //numero de notas maximo q vamos guardar na gravação

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

GFButton teclas[] = {
  GFButton(A8), //azul
  GFButton(A15), //amarelo
  GFButton(A0), //preto
  GFButton(A2), //azul
  GFButton(A3), //preto
  GFButton(A4),  //amarelo
  GFButton(A5) //azul
};

// Botões de controle
GFButton botao_play_pause(A11); //verde
GFButton botao_gravacao(A13); //vermelho

const int NUM_TECLAS = 7;
String notas[] = {"DO", "RE", "MI", "FA", "SOL", "LA", "SI"};


enum Estado { 
  NAVEGANDO, 
  EDITANDO 
};
Estado estadoAtual = NAVEGANDO;


const int NUM_ITENS = 3;
const char* itensMenu[NUM_ITENS] = {"BPM", "Estilo", "Inst."};
int cursorMenu = 0; // começa do BPM


int valorBPM = 100;


const int NUM_ESTILOS = 4;
const char* listaEstilos[NUM_ESTILOS] = {"Rock", "Jazz", "Samba", "Opcao IA"};
int estiloAtual = 0; //default rock


const int NUM_INSTRUMENTOS = 5;
const char* listaInstrumentos[NUM_INSTRUMENTOS] = {"Orgao", "Flauta", "Guitarra", "Bateria", "Piano"};
int instrumentoAtual = 0; //default orgao

volatile int encoderDelta = 0; // a marcação volatile indica ser uma variavel 
// de mudança constante, o sistema guarda essa avriavel em um registardor especial


bool botaoPressionado = false;
bool telaModificada = true;

bool estado_play_pause = false;
bool estado_gravacao = false;

// precisam ser unsigned long pq vai guardar conteudo da millis
unsigned long tempoUltimoBotao = 0; 
unsigned long DEBOUNCE_MS = 200;


// Gravação
int gravacao[MAX_NOTAS]; // qual nota (numero de 0 a 6) foi tocada em cada posição
unsigned long tempos[MAX_NOTAS]; // duração de cada nota
unsigned long pausas[MAX_NOTAS]; // pausa antes de cada nota
int total_de_notas = 0;


unsigned long tempo_inicio = 0; // quando a nota atual começou
unsigned long tempo_ultimo_release = 0; // quando a última nota foi solta


CRGB leds[NUM_LEDS]; //a gente escerve nessa lista e ai FastLED manda pra fita de led


// os Handlers precisam ser 7 funções separadas por causa da biblioteca GFButton
// como a GFButton nao aceita parametros, temos que chamar uma função 
// para cada tecla presssionada 
void whenPressed0() { tecla_pressed(0); }
void whenPressed1() { tecla_pressed(1); }
void whenPressed2() { tecla_pressed(2); }
void whenPressed3() { tecla_pressed(3); }
void whenPressed4() { tecla_pressed(4); }
void whenPressed5() { tecla_pressed(5); }
void whenPressed6() { tecla_pressed(6); }

void whenReleased0() { tecla_released(0); }
void whenReleased1() { tecla_released(1); }
void whenReleased2() { tecla_released(2); }
void whenReleased3() { tecla_released(3); }
void whenReleased4() { tecla_released(4); }
void whenReleased5() { tecla_released(5); }
void whenReleased6() { tecla_released(6); }


// Arrays de ponteiros para funções, pra gente poder chamar a função certa dependendo da tecla
void (*handlersPress[])()   = {whenPressed0, whenPressed1, whenPressed2, whenPressed3,
                               whenPressed4, whenPressed5, whenPressed6};
void (*handlersRelease[])() = {whenReleased0, whenReleased1, whenReleased2, whenReleased3,
                               whenReleased4, whenReleased5, whenReleased6};


void tecla_pressed(int i) {
  leds[i] = CRGB(255, 0, 0);
  FastLED.show();
  Serial.println("{\"nota\": \"" + notas[i] + "\", \"ativa\": true}");

  if (estado_gravacao && total_de_notas < MAX_NOTAS) {
    pausas[total_de_notas] = millis() - tempo_ultimo_release;
    tempo_inicio = millis();
    gravacao[total_de_notas] = i;
    total_de_notas++;
  }
}

void tecla_released(int i) {
  leds[i] = CRGB(0, 0, 0);
  FastLED.show();
  Serial.println("{\"nota\": \"" + notas[i] + "\", \"ativa\": false}");

  if (estado_gravacao && total_de_notas > 0) {
    tempos[total_de_notas - 1] = millis() - tempo_inicio;
    tempo_ultimo_release = millis();
  }
}

void whenPressedPlayPause() {
  estado_play_pause = !estado_play_pause;
  leds[7] = estado_play_pause ? CRGB(255, 0, 0) : CRGB(0, 0, 0);
  FastLED.show();

  if (!estado_play_pause) return;

  // Envia gravação pela serial em JSON
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

  // Reproduz nos LEDs
  for (int i = 0; i < total_de_notas; i++) {
    delay(pausas[i]);
    leds[gravacao[i]] = CRGB(0, 0, 255);
    FastLED.show();
    delay(tempos[i]);
    leds[gravacao[i]] = CRGB(0, 0, 0);
    FastLED.show();
  }
}

void whenPressedGravacao() {
  if (!estado_gravacao) {
    total_de_notas = 0;
    tempo_ultimo_release = millis();
  }
  estado_gravacao = !estado_gravacao;
  leds[8] = estado_gravacao ? CRGB(255, 0, 0) : CRGB(0, 0, 0);
  FastLED.show();
}


void ISR_encoder() {
  if (digitalRead(ENC_DT) == HIGH) {
    encoderDelta++;
  } else {
    encoderDelta--;
  }
}

void processarEncoder() {
  int delta;
  noInterrupts();
  delta = encoderDelta;
  encoderDelta = 0;
  interrupts();

  if (delta == 0) return;

  if (estadoAtual == NAVEGANDO) {
    cursorMenu = constrain(cursorMenu + delta, 0, NUM_ITENS - 1);
  } else {
    switch (cursorMenu) {
      case 0: {  
        int deltaAbs = abs(delta);
        int mult = 1;
        if (deltaAbs >= 5) mult = 5;      
        else if (deltaAbs >= 3) mult = 2;  
        valorBPM = constrain(valorBPM + delta * mult, 20, 300);
        break;
      }
      case 1:  
        estiloAtual = constrain(estiloAtual + delta, 0, NUM_ESTILOS - 1);
        break;
      case 2:  
        instrumentoAtual = constrain(instrumentoAtual + delta, 0, NUM_INSTRUMENTOS - 1);
        break;
    }
    if (cursorMenu == 0) imprimirEstadoSerial();
  }
  telaModificada = true;
}

void lerBotao() {
  bool leitura = (digitalRead(ENC_SW) == LOW);
  if (leitura && !botaoPressionado && (millis() - tempoUltimoBotao > DEBOUNCE_MS)) {
    botaoPressionado = true;
    tempoUltimoBotao = millis();

    estadoAtual = (estadoAtual == NAVEGANDO) ? EDITANDO : NAVEGANDO;
    if (estadoAtual == NAVEGANDO) {
      imprimirEstadoSerial(); 
    }
    telaModificada = true;
  }
  if (!leitura) botaoPressionado = false;
}

void desenharMenu() {
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("- MENU -   - ATUAL -");

  // Linhas 1-3: as 3 opções
  for (int i = 0; i < NUM_ITENS; i++) {
    int linha = i + 1;
    lcd.setCursor(0, linha);

    if (i == cursorMenu) lcd.write(byte(0));
    else lcd.print(" ");

    lcd.print(itensMenu[i]);
    lcd.setCursor(8, linha);

    char abre, fecha;
    if (i == cursorMenu && estadoAtual == EDITANDO) {
      abre = '<'; fecha = '>';
    } else {
      abre = '['; fecha = ']';
    }

    lcd.print(abre);

    String valor;
    if (i == 0)      valor = String(valorBPM);
    else if (i == 1) valor = listaEstilos[estiloAtual];
    else             valor = listaInstrumentos[instrumentoAtual];

    if (valor.length() > 10) valor = valor.substring(0, 10);
    while (valor.length() < 10) valor += ' ';
    lcd.print(valor);

    lcd.print(fecha);
  }
}

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


void setup() {
  Serial.begin(9600);

  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT,  INPUT_PULLUP);
  pinMode(ENC_SW,  INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_CLK), ISR_encoder, FALLING);

  //configuração da fita led
  FastLED.addLeds<WS2812, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.clear(); // zera todo o array leds[] (deixa tudo preto)
  FastLED.show(); //efetivamente envia os dados pra fita

  lcd.init();
  lcd.backlight();
  lcd.createChar(0, charSeta);
  lcd.clear();

  telaModificada = true;
  imprimirEstadoSerial();

  //"Casa" cada tecla com seu handler. Em português: 
  // "tecla[0], quando você for pressionada, chame handlersPress[0]"
  for (int i = 0; i < NUM_TECLAS; i++) {
    teclas[i].setPressHandler(handlersPress[i]);
    teclas[i].setReleaseHandler(handlersRelease[i]);
  }

  // só configura press e não tem release, quando você solta o play, nada acontece
  botao_play_pause.setPressHandler(whenPressedPlayPause);
  botao_gravacao.setPressHandler(whenPressedGravacao);
}

void loop() {
  processarEncoder();
  lerBotao();
  if (telaModificada) {
    desenharMenu();
    telaModificada = false;
  }

  // por baixo dos panos o process:
  // Lê o estado do pino (pressionado ou solto?)
  // Aplica debounce (ignora ruído dos contatos elétricos)
  // Se detectou uma mudança real, chama o handler correspondente
  for (int i = 0; i < NUM_TECLAS; i++) {
    teclas[i].process();
  }
  botao_play_pause.process();
  botao_gravacao.process();
}