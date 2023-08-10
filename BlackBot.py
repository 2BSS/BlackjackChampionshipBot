import cv2
import ctypes
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
import time
import pyautogui
import PySimpleGUI as sg
import pynput
from pynput.mouse import Button, Controller
from pynput import keyboard
from win32gui import GetForegroundWindow, GetWindowText
from PIL import Image
import re
import json
import os

# 

global cardAmount
global strategyChart
with open('strategy.json') as jsonChart:
    strategyChart = json.load(jsonChart)

# Tools -------------------------------------

def TakeScreenshot(LocationX :int, LocationY :int, SizeX :int, SizeY :int, filename :str, grayScale :bool):
    if grayScale:
        image = pyautogui.screenshot(region=(LocationX, LocationY, SizeX, SizeY)).convert("L")
    else:
        image = pyautogui.screenshot(region=(LocationX, LocationY, SizeX, SizeY))
    image.save(r'Images/' + filename + '.png')

def ReadImage(filename):
    img = cv2.imread('Images/' + filename + '.png')
    text = pytesseract.image_to_string(img , config="--psm 6")
    text = re.sub(r'[^a-zA-Z0-9]', '', text)
    return text

def ReadImageNumber(filename):
    img = cv2.imread('Images/' + filename + '.png')
    text = pytesseract.image_to_string(img , config="--oem 3 --psm 6 outputbase digits")
    text = re.sub(r'[^a-zA-Z0-9]', '', text)
    return text

def GetColorFromImage(fileName):
    imagePath = 'Images/' + fileName + '.png'
    image = Image.open(imagePath)
    dominantColor = image.getpixel((0, 0))
    return dominantColor

def MouseClick(x, y):
    originalMouseX, originalMouseY = pyautogui.position()
    pyautogui.click(x, y)
    pyautogui.moveTo(originalMouseX, originalMouseY)

def CardToValue(card):
    if (card in ['J', 'Q', 'K']):
        return "10"
    else:
        return card

# /Tools -------------------------------------
# Game Logic -------------------------------------


def SetSeat():
    while True:
        seat = input("Enter your seat (left/center/right): ").upper()
        if seat in ["LEFT", "CENTER", "RIGHT"]:
            return seat
        else:
            print("Incorrect input. Please enter left, center, or right.")

def Bet(lossStreak):
    betAmountArray = [10, 20, 40, 80, 160, 320]
    raiseClicksArray = [0, 1, 3, 7, 15, 31]
    MouseClick(2350, 1320)
    time.sleep(0.5)
    for i in range(raiseClicksArray[lossStreak]):
        MouseClick(2440, 1100)
        time.sleep(0.1)
    time.sleep(0.5)
    MouseClick(2350, 1320)

def GetMyTurn():
    betButtonColor = (243, 187, 0)
    TakeScreenshot(2300, 1259, 3, 3, "turnFinder", False)
    if (GetColorFromImage("turnFinder") == betButtonColor):
        return True
    else:
        return False
        
def GetCanHit():
    hitButtonColor = (0, 180, 255)
    insureButtonColor = (1, 1, 1)
    TakeScreenshot(2300, 1259, 3, 3, "turnFinder", False)
    if (GetColorFromImage("turnFinder") == hitButtonColor):
        return "HIT"
    elif (GetColorFromImage("turnFinder") == insureButtonColor):
        return "INSURE"
    else:
        return False

def ReadDealerCard():
    TakeScreenshot(1163, 55, 60, 75, "dealerCard", True)
    dealerCard = ReadImage("dealerCard")
    return dealerCard

def ReadMyCards():
    global cardAmount
    myCards = []
    firstCardXCoords = [1965, 1911, 1864, 1817]
    cardTotalXCoords  = [2235, 2280, 2325, 2370]
    for i in range(cardAmount):
        TakeScreenshot(firstCardXCoords[cardAmount-2]+(93*i), 200, 94, 94, "myCard" + str(i), True)
    TakeScreenshot(cardTotalXCoords[cardAmount-2], 170, 70, 55, "myCardTotal", True)
    print("cardAmount: " + str(cardAmount))
    for i in range(cardAmount):
        myCards.append(ReadImage("myCard" + str(i)))
    myCardTotal = ReadImageNumber("myCardTotal")

    return [myCards, myCardTotal]

def GetBestMove(dealerCard, myHand):
    dealerCard = CardToValue(dealerCard)
    bestMove = strategyChart["Dealer"][dealerCard]["Hard"][myHand[1]]
    return bestMove

def CheckForWin():
    TakeScreenshot(2040, 410, 165, 65, "winCheck", True)
    winMessage = ReadImage("winCheck")
    return winMessage

def DecideAction():
    global cardAmount
    dealerCard = ReadDealerCard()
    myHand = ReadMyCards()
    if dealerCard and not any(card == "" for card in myHand):
        bestMove = GetBestMove(dealerCard, myHand)
        print("Dealer upcard: " + dealerCard)
        print("My cards: " + str(myHand[0]) + " for a total of " + myHand[1])
        print("The best move is " + bestMove)
        if (bestMove == "H"):
            MouseClick(2350, 1320)
            cardAmount += 1
            return "H"
        elif (bestMove == "S"):
            MouseClick(2000, 1300)
            cardAmount = 2
            myHand = []
            return "S"
    else: 
        print("ERROR: Failed to read cards from screen!")
        print("dealerCard: " + dealerCard)
        print("myHand: " + str(myHand[0]))
        print("myHandTotal: " + myHand[1])
    return

# /Game Logic -------------------------------------

def Main():
    makingMove = False
    lossStreak = 0
    while True:
        if (GetMyTurn() and not makingMove):
            makingMove = True
            Bet(lossStreak)
            waitingForHit = True

            while waitingForHit:
                canHit = GetCanHit()
                if (canHit == "HIT"):
                    action = DecideAction()

                    if (action == "H"):
                        print("Hit")
                        time.sleep(1.5)

                        if(CheckForWin() == "BUST"):
                            waitingForHit = False
                            makingMove = False
                    elif (action == "S"):
                        print("Stand")
                        waitingForHit = False
                        time.sleep(2)
                        print(CheckForWin())
                elif canHit == "INSURE":
                    MouseClick()
                else:
                    print("Waiting for my turn")
                    time.sleep(1)
            makingMove = False
            time.sleep(1)
        else:
            print("Waiting for next round")
            time.sleep(1)

seat = SetSeat()
print("Seat " + seat + " set!")
cardAmount = 2
Main()