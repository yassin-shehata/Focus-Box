import os
from wavePlayer import wavePlayer
from machine import Pin, SPI, ADC
from ili9341 import Display, color565
from time import sleep
import xglcd_font
from hcsr04 import HCSR04
import tm1637
import time
import utime

# Function definitions from the first code
def read_user_feeling():
    adc_value = pot.read_u16()
    user_feeling = min(adc_value, 60000)
    user_feeling = user_feeling / 10000.0
    return user_feeling

def draw_text_on_display(text1, text2):
    display.draw_text(70, 220, text1, arcadepix, color565(255, 255, 255), landscape=True)
    display.draw_text(220, 150, text2, arcadepix, color565(255, 255, 255), landscape=True)

def ask_meal_status():
    display.clear()
    display.draw_text(70, 220, "Have you had your meal?", arcadepix, color565(255, 255, 255), landscape=True)
    display.draw_text(220, 150, "Select rating", arcadepix, color565(255, 255, 255), landscape=True)

def main():
    user_feeling = 0.0
    meal_status_asked = False
    day_question_asked = False
    switch_state = True  # Initially assuming the switch is ON
    while True:
        try:
            # Check the state of the switch
            if not machine.Pin(16).value():  # If the switch is OFF
                print("Switch OFF, restarting the program...")
                return  # Exit the main function to restart the program

            if not meal_status_asked and user_feeling > 4:
                ask_meal_status()
                meal_status_asked = True
            elif meal_status_asked:
                meal_rating = read_user_feeling()
                print("Meal Rating:", round(meal_rating, 1))
                if meal_rating < 4:
                    meal_status_asked = False
                    user_feeling = meal_rating
                else:
                    display.draw_text(220, 150, "Meal Rating: {:.1f}".format(meal_rating), arcadepix, color565(255, 255, 255), landscape=True)
                    sleep(1)
                    display.clear()
                    display.draw_text(70, 220, "Great! Have a nice day!", arcadepix, color565(255, 255, 255), landscape=True)
                    sleep(2)
                    measure_heartbeat_and_execute_device_code()  # Start heartbeat detection after displaying the message
                    meal_status_asked = False
                    day_question_asked = False
            else:
                if not day_question_asked:
                    user_feeling = read_user_feeling()
                    print("User Feeling:", round(user_feeling, 2))
                    text1 = "Hey, how was your day?"
                    text2 = "User Feeling: {:.1f}".format(user_feeling)
                    draw_text_on_display(text1, text2)
                    day_question_asked = True
                else:
                    user_feeling = read_user_feeling()
                    print("User Feeling:", round(user_feeling, 2))
                    text2 = "User Feeling: {:.1f}".format(user_feeling)
                    draw_text_on_display("", text2)
            sleep(2)

        except Exception as e:
            print("An error occurred:", e)

# Code from the second script
adcpin = 26
pot = ADC(adcpin)
spi = SPI(1, baudrate=40000000, sck=Pin(14), mosi=Pin(15))
display = Display(spi, dc=Pin(6), cs=Pin(17), rst=Pin(7))
arcadepix = xglcd_font.XglcdFont('ArcadePix9x11.c', 9, 11)
sensor1 = HCSR04(trigger_pin=10, echo_pin=11, echo_timeout_us=10000)
sensor2 = HCSR04(trigger_pin=0, echo_pin=1, echo_timeout_us=10000)
tm = tm1637.TM1637(clk=Pin(5), dio=Pin(4))
adc = ADC(Pin(28))
motor = Pin(13, Pin.OUT) # Make sure your GPIO pin is connected to the base of the transistor

MAX_HISTORY = 150

def measure_heartbeat_and_execute_device_code():
    global history
    history = []
    while True:
        v = adc.read_u16()
        history.append(v)
        history = history[-MAX_HISTORY:]
        minima, maxima = min(history), max(history)
        vpower = v / maxima
        ledtemp = 0.6 if vpower < 0.7 else 1
        time.sleep(0.1)

        if ledtemp == 0.6:
            print("Heartbeat reached 0.6, proceeding with device code.")
            execute_device_code()
            break

def execute_device_code():
    while True:
        distance1 = sensor1.distance_cm()
        if distance1 >= 0:
            print('Distance Sensor 1:', distance1, 'cm')

            if distance1 < 5:
                print("Distance below 5 cm detected by sensor 1")

                while True:
                    distance2 = sensor2.distance_cm()
                    if distance2 >= 0:
                        print('Distance Sensor 2:', distance2, 'cm')

                        if distance2 < 5:
                            print("Distance below 5 cm detected by sensor 2")
                            start_timer()
                            return

                    time.sleep(0.5)

        time.sleep(0.5)

def start_timer():
    print("Timer started")
    
    # Re-initialize the LED display
    tm = tm1637.TM1637(clk=Pin(5), dio=Pin(4))
    
    # Run the motor for 2 seconds
    motor.on()
    time.sleep(2)
    motor.off()
    print("Motor ran for 2 seconds")
    
    for remaining in range(8, -1, -1):  # Counting down from 8 to 0 (total 9 seconds remaining)
        minutes = remaining // 60
        seconds = remaining % 60
        tm.numbers(minutes, seconds)
        time.sleep(1)
    
    # Run the motor for 2 seconds again when timer ends
    motor.on()
    time.sleep(2)
    motor.off()
    print("Motor ran for 2 seconds after the timer ended")
    
    tm.number(0)
    print("Timer ended")
    display.clear()
    display.draw_text(100, 100, "Timer Ended", arcadepix, color565(255, 255, 255), landscape=True)
    sleep(2)
    
    # Play audio
    audio_file = "p_18726648_72-compressed.wav"  # Replace "your_audio_file.wav" with the actual path to your audio file
    player = wavePlayer()
    player.play(audio_file)
    
    print("Let's measure your heartbeat")



def integrate_and_repeat():
    # Initialize the rocker switch pin
    Rocker_Sw = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_DOWN)
    LED = machine.Pin(25, machine.Pin.OUT)  # LED to indicate switch state

    while True:
        try:
            # Poll the rocker switch
            if Rocker_Sw.value():  # If the switch is ON
                LED.value(1)  # Turn on LED
                print("Switch ON")

                # Call the main function
                main()

                # After main function execution, clear display and indicate timer done
                display.clear()
                display.draw_text(100, 100, "Timer Done", arcadepix, color565(255, 255, 255), landscape=True)
                sleep(2)

            else:  # If the switch is OFF
                LED.value(0)  # Turn off LED
                print("Switch OFF")
                
                # Do nothing, wait until the switch is turned ON again
                while not Rocker_Sw.value():  # Wait until the switch is turned ON
                    utime.sleep(0.1)

        except Exception as e:
            print("An error occurred:", e)

if __name__ == "__main__":
    integrate_and_repeat()

