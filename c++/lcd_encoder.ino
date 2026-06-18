#include <Wire.h>
#include <LiquidCrystal_I2C.h>

//Pinos do encoder
#define ENC_CLK  2
#define ENC_DT   3
#define ENC_SW   4

LiquidCrystal_I2C lcd(0x27, 20, 4);

// desenhados pixel a pixel 5x8
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

//paginas do menu
enum Estado {
  MENU_PRINCIPAL,
  EDITANDO_RITMO,
  EDITANDO_BPM,
  EDITANDO_ESTILO
};

Estado estadoAtual = MENU_PRINCIPAL;

const int NUM_ITENS_MENU = 3;
const char* itensMenu[NUM_ITENS_MENU] = { "Ritmo", "BPM", "Estilo" };
int cursorMenu = 0;

//parametros
int valorRitmo = 10;
int valorBPM = 100;

const int NUM_ESTILOS = 4;
const char* listaEstilos[NUM_ESTILOS] = {
  "Rock", "Jazz", "Samba"
};
int estiloAtual  = 0;
int cursorEstilo = 0;

//encoder
int  ultimoEstadoCLK;
bool botaoPressionado = false;
unsigned long tempoUltimoBotao = 0;
const unsigned long DEBOUNCE_MS = 250;

//feedback
bool mostrandoFeedback = false;
unsigned long tempoFeedback = 0;
const unsigned long DURACAO_FEEDBACK = 1500;
String mensagemFeedback = "";

//controle de tela ---
bool telaModificada = true;

void setup() {
  Serial.begin(9600);

  pinMode(ENC_CLK, INPUT);
  pinMode(ENC_DT,  INPUT);
  pinMode(ENC_SW,  INPUT_PULLUP);
  ultimoEstadoCLK = digitalRead(ENC_CLK);

  lcd.init();
  lcd.backlight();
  lcd.createChar(0, charSeta);//salva a seta
  lcd.createChar(1, charCheck);//salva o check

  lcd.clear();
  telaModificada = true;
  imprimirEstadoSerial("inicio");
}

void loop() {
  lerEncoder();
  lerBotao();
  gerenciarFeedback();

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
      case EDITANDO_RITMO:
        valorRitmo = constrain(valorRitmo + direcao, 1, 12);
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
        if (cursorMenu == 0)      estadoAtual = EDITANDO_RITMO;
        else if (cursorMenu == 1) estadoAtual = EDITANDO_BPM;
        else if (cursorMenu == 2) {
          estadoAtual = EDITANDO_ESTILO;
          cursorEstilo = estiloAtual;
        }
        break;

      case EDITANDO_RITMO:
        ativarFeedback("Ritmo salvo!");
        estadoAtual = MENU_PRINCIPAL;
        imprimirEstadoSerial("ritmo");
        break;

      case EDITANDO_BPM:
        ativarFeedback("BPM salvo!");
        estadoAtual = MENU_PRINCIPAL;
        imprimirEstadoSerial("bpm");
        break;

      case EDITANDO_ESTILO:
        estiloAtual = cursorEstilo;
        ativarFeedback("Estilo salvo!");
        estadoAtual = MENU_PRINCIPAL;
        imprimirEstadoSerial("estilo");
        break;
    }
    telaModificada = true;
  }

  if (!leitura) botaoPressionado = false;
}

void ativarFeedback(const char* msg) {
  mostrandoFeedback = true;
  tempoFeedback = millis();
  mensagemFeedback = msg;
}

void gerenciarFeedback() {
  if (mostrandoFeedback && (millis() - tempoFeedback > DURACAO_FEEDBACK)) {
    mostrandoFeedback = false;
    telaModificada = true;
  }
}

void desenharTela() {
  lcd.clear();

  switch (estadoAtual) {
    case MENU_PRINCIPAL:    desenharMenuPrincipal();  break;
    case EDITANDO_RITMO:    desenharEditorRitmo();    break;
    case EDITANDO_BPM:      desenharEditorBPM();      break;
    case EDITANDO_ESTILO: desenharSeletorEstilo();  break;
  }

  if (mostrandoFeedback) {
    lcd.setCursor(0, 3);
    lcd.print("                    ");
    lcd.setCursor(0, 3);
    lcd.write(byte(1));
    lcd.print(" ");
    lcd.print(mensagemFeedback);
  }
}

void desenharMenuPrincipal() {
  lcd.setCursor(0, 0);
  lcd.print("- MENU -   - ATUAL -");

  for (int i = 0; i < NUM_ITENS_MENU; i++) {
    lcd.setCursor(0, i + 1);

    if (i == cursorMenu) lcd.write(byte(0)); 
    else                 lcd.print(" ");

    lcd.print(itensMenu[i]);

    lcd.setCursor(11, i + 1);
    if (i == 0) {
      lcd.print("[");
      lcd.print(valorRitmo);
      lcd.print("]");
    } else if (i == 1) {
      lcd.print("[");
      lcd.print(valorBPM);
      lcd.print("]");
    } else {
      lcd.print("[");
      String est = listaEstilos[estiloAtual];
      if (est.length() > 6) est = est.substring(0, 6);
      lcd.print(est);
      lcd.print("]");
    }
  }
}

void desenharEditorRitmo() {
  lcd.setCursor(0, 0);
  lcd.print("-> Ritmo");

  lcd.setCursor(2, 1);
  lcd.print("Compasso: [");
  lcd.print(valorRitmo);
  lcd.print("]");

  if (!mostrandoFeedback) {
    lcd.setCursor(0, 2);
    lcd.print("Gire para alterar");
    lcd.setCursor(0, 3);
    lcd.print("Clique para salvar");
  }
}

void desenharEditorBPM() {
  lcd.setCursor(0, 0);
  lcd.print("-> BPM");

  lcd.setCursor(2, 1);
  lcd.print("Velocidade: [");
  lcd.print(valorBPM);
  lcd.print("]");

  if (!mostrandoFeedback) {
    lcd.setCursor(0, 2);
    lcd.print("Gire para alterar");
    lcd.setCursor(0, 3);
    lcd.print("Clique para salvar");
  }
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

void imprimirEstadoSerial(const char* evento) {
  Serial.print("{");

  Serial.print("\"evento\":\"");    
  Serial.print(evento);                     
  Serial.print("\"");

  Serial.print(",\"ritmo\":");      
  Serial.print(valorRitmo);

  Serial.print(",\"bpm\":");        
  Serial.print(valorBPM);

  Serial.print(",\"estilo\":\"");   
  Serial.print(listaEstilos[estiloAtual]);  
  Serial.print("\"");

  Serial.print(",\"compasso\":"); 
  Serial.print(valorRitmo);                

  Serial.println("}");
}