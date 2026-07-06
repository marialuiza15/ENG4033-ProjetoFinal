#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define ENC_CLK  2   
#define ENC_DT   3  
#define ENC_SW   4

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

enum Estado { NAVEGANDO, EDITANDO };
Estado estadoAtual = NAVEGANDO;

const int NUM_ITENS = 3;

const char* itensMenu[NUM_ITENS] = {"BPM", "Estilo", "Inst."};
int cursorMenu = 0;

int valorBPM = 100;

// Estilos
const int NUM_ESTILOS = 4;
const char* listaEstilos[NUM_ESTILOS] = {
  "Rock", "Jazz", "Samba", "Opcao IA"
};
int estiloAtual = 0;

const int NUM_INSTRUMENTOS = 5;

const char* listaInstrumentos[NUM_INSTRUMENTOS] = {
  "Orgao", "Flauta", "Guitarra", "Bateria", "Piano"
};
int instrumentoAtual = 0;

volatile int encoderDelta = 0;

bool botaoPressionado = false;
unsigned long tempoUltimoBotao = 0;
const unsigned long DEBOUNCE_MS = 200;

bool telaModificada = true;

void ISR_encoder() {
  if (digitalRead(ENC_DT) == HIGH) {
    encoderDelta++;
  } else {
    encoderDelta--;
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT,  INPUT_PULLUP);
  pinMode(ENC_SW,  INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENC_CLK), ISR_encoder, FALLING);

  lcd.init();
  lcd.backlight();
  lcd.createChar(0, charSeta);
  lcd.clear();

  telaModificada = true;
  imprimirEstadoSerial();
}

void loop() {
  processarEncoder();
  lerBotao();
  if (telaModificada) {
    desenharMenu();
    telaModificada = false;
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

