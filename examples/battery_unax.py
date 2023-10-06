"""Example of using a battery for economic and carbon optimization."""
import energypylinear as epl
import pandas as pd

#  input interval data
electricity_prices = [
    53.30, 
    52.57, 
    41.02, 
    39.49, 
    39.48, 
    38.47,
    59.12, 
    60.14, 
    74.74, 
    74.74, 
    79.36, 
    81.46, 
    81.49, 
    81.55, 
    101.13, 
    101.14, 
    122.83, 
    123.26, 
    122.58, 
    119.30, 
    119.27, 
    115.80, 
    99.16, 
    98.47,
     
    ]

#  battery model
asset = epl.Battery(power_mw=3.3, capacity_mwh=7, efficiency=1)

df = pd.read_csv('day_ahead.csv', header=None, names=['value'])
print (df)

# Iterate through the DataFrame in batches of 24 consecutive values
batch_size = 24
num_batches = len(df) // batch_size
print (num_batches)
day = 0
for i in range(num_batches):
    batch_start = i * batch_size
    batch_end = (i + 1) * batch_size
    batch = df.iloc[batch_start:batch_end]
    
    # Print the batch of 24 consecutive values
    day = day +1

#  optimize for money
results = asset.optimize(
    electricity_prices=electricity_prices,
    final_charge_mwh=7,
)
print("#####")
print(results.simulation["site-import_power_mwh"])
profit = 0
for index, prices in enumerate(electricity_prices):
    price = electricity_prices[index]
    buy = results.simulation["site-import_power_mwh"][index]
    sell = results.simulation["site-export_power_mwh"][index]
    amount = ((-1) * price * buy) + price * sell
    profit += amount
    print (index, buy, sell, amount, profit)
    print ("balance:", profit, ", considering wholesale price:", profit+7.5*102.1)