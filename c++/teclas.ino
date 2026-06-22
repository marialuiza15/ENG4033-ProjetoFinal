#include <FastLED.h>
#include <GFButton.h>

const int NUM_LEDS = 12;
const int DATA_PIN = 7;

//Botão de teclas musicais

GFButton tecla1(A8);
GFButton tecla2(A15);
GFButton tecla3(A0);
GFButton tecla4(A2);
GFButton tecla5(A3);
GFButton tecla6(A4);
GFButton tecla7(A5);

//Botão de funcionalidades extras: play/pause, gravar

GFButton botao_play_pause(A11);
GFButton botao_gravacao(A13);

bool estado_play_pause = false;
bool estado_gravacao = false;

String notas[] = {
  "DO",
  "RE",
  "MI",
  "FA",
  "SOL",
  "LA",
  "SI"
};

int gravacao[300];
int total_de_notas = 0;

unsigned long tempos[300];
unsigned long pausas[300];
unsigned long tempo_inicio = 0;
unsigned long tempo_ultimo_release = 0;

CRGB leds[NUM_LEDS];

void marca_nota(int nota){
    if (estado_gravacao){
        if (total_de_notas < 300) {
            gravacao[total_de_notas] = nota;
            total_de_notas += 1;
        }
    }
}

void tecla_pressed(int i){
    leds[i] = CRGB(255, 0, 0);
    FastLED.show();
    Serial.println("Nota: " + notas[i]);
    if (estado_gravacao) {
        pausas[total_de_notas] = millis() - tempo_ultimo_release;
        tempo_inicio = millis();
    }
    marca_nota(i);
}

void tecla_released(int i){
    leds[i] = CRGB(0, 0, 0);
    FastLED.show();
    if (estado_gravacao) {
        tempos[total_de_notas - 1] = millis() - tempo_inicio;
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
    Serial.println("Play/Pause: " + String(estado_play_pause ? "ATIVO" : "INATIVO"));
    if (estado_play_pause){
        for (int i = 0; i < total_de_notas; i++) {
            delay(pausas[i]);
            Serial.println(notas[gravacao[i]] + ": " + tempos[i]);
            leds[gravacao[i]] = CRGB(0, 0, 255);
            FastLED.show();
            delay(tempos[i]);
            leds[gravacao[i]] = CRGB(0, 0, 0);
            FastLED.show();
        }
    }
}

void whenPressedGravacao() {
    if (!estado_gravacao){
        total_de_notas = 0;
        tempo_ultimo_release = millis();
    }
    estado_gravacao = !estado_gravacao;
    leds[8] = estado_gravacao ? CRGB(255, 0, 0) : CRGB(0, 0, 0);
    FastLED.show();
    Serial.println("Gravacao: " + String(estado_gravacao ? "ATIVA" : "INATIVA"));
}

void setup() {
  Serial.begin(9600);

  FastLED.addLeds<WS2812, DATA_PIN, GRB>(leds, NUM_LEDS);

  FastLED.clear();
  FastLED.show();

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