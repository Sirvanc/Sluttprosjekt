import utime
import gc
from lcd_api import LcdApi
from machine import I2C

# PCF8574 pin-definisjoner
MASK_RS = 0x01       # P0
MASK_RW = 0x02       # P1
MASK_E  = 0x04       # P2

SHIFT_BACKLIGHT = 3  # P3
SHIFT_DATA      = 4  # P4-P7

class I2cLcd(LcdApi):
    # Implementerer en HD44780 karakter LCD koblet via PCF8574 over I2C

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        # Start LCD-en
        self.i2c.writeto(self.i2c_addr, bytes([0]))
        utime.sleep_ms(20)   # Gi LCD tid til å starte opp

        # Send reset 3 ganger for å sette opp LCD-en
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(5)    # Må vente minst 4.1 msec
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(1)

        # Sett LCD-en i 4-bit modus
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        utime.sleep_ms(1)

        # Initialiser LCD-en
        LcdApi.__init__(self, num_lines, num_columns)
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)

        # Rydd opp minne
        gc.collect()

    def hal_write_init_nibble(self, nibble):
        # Skriver en initialisering nibble til LCD-en.
        byte = ((nibble >> 4) & 0x0f) << SHIFT_DATA
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        gc.collect()
        
    def hal_backlight_on(self):
        # Slår på bakgrunnsbelysningen
        self.i2c.writeto(self.i2c_addr, bytes([1 << SHIFT_BACKLIGHT]))
        gc.collect()
        
    def hal_backlight_off(self):
        # Slår av bakgrunnsbelysningen
        self.i2c.writeto(self.i2c_addr, bytes([0]))
        gc.collect()
        
    def hal_write_command(self, cmd):
        # Skriver en kommando til LCD-en. Data blir latchet på falling E-puls.
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                (((cmd >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                ((cmd & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))

        # Home- og clear-kommandoene krever minst 4.1 msec venting
        if cmd <= 3:
            utime.sleep_ms(5)

        gc.collect()

    def hal_write_data(self, data):
        # Skriver data til LCD-en. Data blir latchet på falling E-puls.
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                (((data >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                ((data & 0x0f) << SHIFT_DATA))      
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        gc.collect()
