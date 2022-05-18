#main python file

import datetime
# import coinbase

## for getting updated pricing from the API ##

# from coinbase.wallet.client import Client
# client = Client(<api_key>, <api_secret>)

# price = client.get_buy_price(currency_pair = 'BTC-USD')

print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
print("Welcome to the Bitcoin Investment Disappointment Calculator")
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
print(" ")

print("Enter your name: ")
userName = input()
print(".....")
print(f'Hello, and welcome Rob!') # {userName}
print(" ")
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
print(f'This calculator determines how much money you would have today, if you had invested in Bitcoin in 2013')
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")

print(" ")

initialBitcoinValue = 13.30
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
print(f'The price of Bitcoin in 2013 was ${initialBitcoinValue}')
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
print(f'How much would your initial investment have been in USD? ')
initialInvestment = float(input())


initialNumberOfShares = initialInvestment / initialBitcoinValue
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
print(f'Your initial number of shares would have been {initialNumberOfShares}')
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
currentValueOfBitcoin = 29983.56
print(f'The current value of bitcoin is {currentValueOfBitcoin}')
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
currentValuation = currentValueOfBitcoin * initialNumberOfShares

ferrariCount = currentValuation / 300000
print("|||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")

print(f'Today that would be worth ${currentValuation} or {ferrariCount} Ferrari SuperCars')
print(" ")
print(" ")
print("||||||||||||||||||||||||||||||||||||")
print('Goodbye')