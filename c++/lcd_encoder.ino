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
int instrumentoAtual  = 0;
int cursorInstrumento = 0;

// BPM
int valorBPM = 100;

// Estilos
const int NUM_ESTILOS = 4;
const char* listaEstilos[NUM_ESTILOS] = {
  "Rock", "Jazz", "Samba", "Escolha da IA"
};
int estiloAtual  = 0;
int cursorEstilo = 0;

// Encoder
int  ultimoEstadoCLK;
bool botaoPressionado = false;
unsigned long tempoUltimoBotao = 0;
const unsigned long DEBOUNCE_MS = 250;



bool telaModificada = true;

void setup() {
  Serial.begin(9600);
  pinMode(ENC_CLK, INPUT);
  pinMode(ENC_DT,  INPUT);
  pinMode(ENC_SW,  INPUT_PULLUP);
  ultimoEstadoCLK = digitalRead(ENC_CLK);

  lcd.init();
  lcd.backlight();
  lcd.createChar(0, charSeta);
  lcd.createChar(1, charCheck);
  lcd.clear();
  telaModificada = true;
  imprimirEstadoSerial();
}

void loop() {
  lerEncoder();
  lerBotao();
  if (telaModificada) {
    desenharTela();
    telaModificada = false;
  }
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
        if (cursorMenu == 0) {
          estadoAtual = EDITANDO_BPM;
        } else if (cursorMenu == 1) {
          estadoAtual = EDITANDO_ESTILO;
          cursorEstilo = estiloAtual;
        } else if (cursorMenu == 2) {
          estadoAtual = EDITANDO_INSTRUMENTO;
          cursorInstrumento = instrumentoAtual;
        }
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


void desenharTela() {
  lcd.clear();
  switch (estadoAtual) {
    case MENU_PRINCIPAL:       
      desenharMenuPrincipal();      
      break;
    case EDITANDO_INSTRUMENTO: 
      desenharSeletorInstrumento(); 
      break;
    case EDITANDO_BPM:         
      desenharEditorBPM();          
      break;
    case EDITANDO_ESTILO:      
      desenharSeletorEstilo();      
      break;
  }

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
      lcd.print("[");
      lcd.print(valorBPM);
      lcd.print("]");
    } else if (i == 1) {
      lcd.print("[");
      String est = listaEstilos[estiloAtual];
      if (est.length() > 5) est = est.substring(0, 5);
      lcd.print(est);
      lcd.print("]");
    } else {
      lcd.print("[");
      String inst = listaInstrumentos[instrumentoAtual];
      if (inst.length() > 5) inst = inst.substring(0, 5);
      lcd.print(inst);
      lcd.print("]");
    }
  }
}

void desenharSeletorInstrumento() {
  lcd.setCursor(0, 0);
  lcd.print("-> Instrumento");

  int inicioScroll = 0;
  if (cursorInstrumento >= 3) inicioScroll = cursorInstrumento - 2;

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

  int inicioScroll = 0;
  if (cursorEstilo >= 3) inicioScroll = cursorEstilo - 2;

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

