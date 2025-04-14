from machine import I2C, Pin, PWM
from time import sleep
import random
from pico_i2c_lcd import I2cLcd

# Velg om du vil bruke knapper eller konsoll
USE_BUTTONS = True  # Sett til True for å bruke knapper (False for testing i konsollen)

# Definer pinner for LED, buzzer og knapper
GREEN_LED_PIN = 2  
RED_LED_PIN = 3    
BUZZER_PIN = 4
BUTTON_PARTALL_PIN = 5  
BUTTON_ODD_PIN = 6        

# Initialiser LED og buzzer
green_led = Pin(GREEN_LED_PIN, Pin.OUT)
red_led = Pin(RED_LED_PIN, Pin.OUT)
buzzer = PWM(Pin(BUZZER_PIN))

# Initialiser knapper hvis de er i bruk
if USE_BUTTONS:
    button_partall = Pin(5, Pin.IN, Pin.PULL_UP)  # Pull-up motstand
    button_odd = Pin(6, Pin.IN, Pin.PULL_UP)          # Pull-up motstand

# Grenser for spill
MAX_SCORE = 7  
MAX_ATTEMPTS = 3  

# Poengsum og forsøk
score = 0
attempts = 0
correct_streak = 0  # Teller for antall riktige svar på rad

def beep(varighet=0.1, frekvens=1000):
    """Kort pip for riktig svar."""
    buzzer.freq(frekvens)
    buzzer.duty_u16(30000)
    sleep(varighet)
    buzzer.duty_u16(0)

def feil_beep(varighet=0.5, frekvens=500):
    """Langt pip for feil svar.""" 
    buzzer.freq(frekvens)
    buzzer.duty_u16(30000)
    sleep(varighet)
    buzzer.duty_u16(0)

def nederlagtone():
    """Spiller en trist tone ved tap."""
    for frekvens in [500, 400, 300]:
        buzzer.freq(frekvens)
        buzzer.duty_u16(30000)
        sleep(0.3)
    buzzer.duty_u16(0)

def seierstone():
    """Spiller en enkel seierstone."""
    for frekvens in [1000, 1200, 1500]:
        buzzer.freq(frekvens)
        buzzer.duty_u16(30000)
        sleep(0.2)
    buzzer.duty_u16(0)

def dansetone():
    """Spiller en 'dansetone' som belønning."""
    for frekvens in [1500, 1800, 2000, 2200]:
        buzzer.freq(frekvens)
        buzzer.duty_u16(30000)
        sleep(0.1)
    buzzer.duty_u16(0)

def blink_grønn_led(antall=3):
    """Blinker grønn LED flere ganger."""
    for _ in range(antall):
        green_led.value(1)
        sleep(0.2)
        green_led.value(0)
        sleep(0.2)

def initialiser_i2c_lcd(sda_pin=0, scl_pin=1, i2c_frekvens=400000, lcd_adresse=0x27):
    """Initialiser I2C LCD-skjerm."""
    try:
        # Initialiser I2C
        i2c_buss = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=i2c_frekvens)
        enheter = i2c_buss.scan()
        if lcd_adresse not in enheter:
            print("🚨 LCD ikke funnet! Sjekk kabling.")
            return None
        lcd = I2cLcd(i2c_buss, lcd_adresse, 2, 16)  # Initialiser LCD-en med 2 linjer og 16 kolonner
        return lcd
    except Exception as e:
        print(f"🚨 Feil ved LCD-initialisering: {e}")
        return None

def vis_melding(lcd, melding, forsinkelse=2):
    """Vis melding på LCD."""
    if lcd:
        lcd.clear()
        lcd.putstr(melding)
    print(melding)  # Skriver ut i konsollen for debugging
    sleep(forsinkelse)

def hent_bruker_valg():
    """Les brukerens valg fra knapper."""
    print("Venter på knappetrykk...")

    while True:
        # Vent på at en av knappene blir trykket
        if button_partall.value() == False:  # Hvis knappen for partall er trykket (aktiv lav)
            sleep(0.2)  # Litt forsinkelse for å unngå prell
            return 'p'  # Returner 'p' for partall
        if button_odd.value() == False:  # Hvis knappen for oddetall er trykket (aktiv lav)
            sleep(0.2)
            return 'o'  # Returner 'o' for oddetall

def spill_spill(lcd):
    """Hovedlogikk for spillet."""
    global score, attempts, correct_streak, spill_status
    spill_status = False
    while not spill_status:  # Bruker "not spill_status" for at loopen kan fortsette
        if attempts >= MAX_ATTEMPTS:
            vis_melding(lcd, "Tapt! Spillet er over!! 😢")
            nederlagtone()
            # Lyse rød LED i 2 sekunder for å indikere tap
            red_led.value(1)
            sleep(2)
            red_led.value(0)
            sleep(2)
            vis_melding(lcd, "Spillet starter\npå nytt!")
            score = 0
            attempts = 0
            correct_streak = 0
            # Start en ny runde uten å sette spill_status til True (det skal fortsette å gå)
        
        if score >= MAX_SCORE:
            # Spilleren har nådd maks poengsum, vis flere "DU VANT!" på skjermen
            for _ in range(3):  # Vise "DU VANT!" 3 ganger
                vis_melding(lcd, "Gratulerer - du vant! Hurra 🎉", forsinkelse=1)
            
            # Spill seierstone og blink grønn LED flere ganger
            seierstone()
            blink_grønn_led(antall=6)  # Blink grønn LED 6 ganger
            score = 0
            attempts = 0
            correct_streak = 0
            vis_melding(lcd, "Ny runde!\nTrykk P eller O.")
        
        tall = random.randint(1, 100)
        vis_melding(lcd, f"Er {tall}\n(P)artall / (O)dd?")

        bruker_input = hent_bruker_valg()
        print(f"Du valgte: {bruker_input}")

        riktig = (bruker_input == 'p' and tall % 2 == 0) or (bruker_input == 'o' and tall % 2 != 0)
    
        if riktig:
            vis_melding(lcd, "Riktig! +1 poeng")
            green_led.value(1)
            beep()
            score += 1
            correct_streak += 1  # Øker streak ved riktig svar
            # Belønn spilleren for å ha flere riktige svar på rad
            if correct_streak >= 3:
                vis_melding(lcd, "Bonus! +2 poeng!")
                score += 2  # Gir bonuspoeng
                dansetone()  # Spiller dansetone
                blink_grønn_led()  # Blinker grønn LED
                correct_streak = 0  # Resetter streaken etter bonus
        else:
            vis_melding(lcd, "Feil! -1 poeng")
            red_led.value(1)  # Tenne rød LED når spiller feiler
            feil_beep()
            sleep(1)  # LED-en vil lyse i 1 sekund for feil
            red_led.value(0)  # Slå av rød LED
            score -= 1
            attempts += 1
            correct_streak = 0  # Resetter streak ved feil svar

        sleep(2)
        green_led.value(0)
        vis_melding(lcd, f"Poeng: {score}\nNeste tall...")

def hovedprogram():
    """Starter spillet."""
    lcd = initialiser_i2c_lcd()
    if lcd is None:
        print("🚨 LCD ikke funnet, kjører uten skjerm.")
    
    vis_melding(lcd, "Velkommen til Partall eller Oddetall-spill!\nTrykk P (Partall) / O (Oddetall).")
    spill_spill(lcd)

if __name__ == '__main__':
    hovedprogram()
