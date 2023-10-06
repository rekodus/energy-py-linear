"""Example of using a battery for economic and carbon optimization."""
# python battery_unax2.py | grep "###"
import energypylinear as epl
import pandas as pd

# number of cars per month
no_chargers = 300
kwh_per_car = 30
power_mw = 11 * no_chargers / 1000
capacity_mw = no_chargers * kwh_per_car / 1000
final_charge_mwh = no_chargers * kwh_per_car / 1000
efficiency = 0.9
wholesale_price_mwh = 88.4  # 2024: 91.0, 2028: 69.0, 2025: 88.4
use_fcr = False
fcr_price_mw = 18.2 # 2024: 53.4, 2028: 18.2
fcr_acceptance_rate = 0.8
#price_curve_file = 'intraday_2028.csv'
price_curve_file = 'day_ahead_2025.csv'

#  battery model
asset = epl.Battery(power_mw=power_mw, capacity_mwh=capacity_mw, efficiency=efficiency)

#df = pd.read_csv('day_ahead.csv', header=None, names=['value'])
df = pd.read_csv(price_curve_file, header=None, names=['value'])
print (df)

# Iterate through the DataFrame in batches of 24 consecutive values
batch_size = 24
num_batches = len(df) // batch_size
print ("***", num_batches)

yearly_profit = 0
yearly_balance = 0
yearly_fcr_revenue = 0
for day in range(num_batches):
    batch_start = day * batch_size
    batch_end = (day + 1) * batch_size
    electricity_prices = df.iloc[batch_start:batch_end].values
    #  optimize for money
    results = asset.optimize(
        electricity_prices=electricity_prices,
        final_charge_mwh=final_charge_mwh,
    )

    daily_profit = 0
    daily_balance = 0
    daily_fcr_revenue = 0
    for index, prices in enumerate(electricity_prices):
        price = electricity_prices[index]
        buy = results.simulation["site-import_power_mwh"][index]
        sell = results.simulation["site-export_power_mwh"][index]
        amount = ((-1) * price * buy) + price * sell
        daily_balance+= amount
        if use_fcr and buy == 0 and sell ==0:
            daily_fcr_revenue += fcr_acceptance_rate * fcr_price_mw * power_mw
    daily_profit = daily_balance + wholesale_price_mwh * final_charge_mwh + daily_fcr_revenue
    yearly_balance += daily_balance
    yearly_fcr_revenue += daily_fcr_revenue
    yearly_profit += daily_profit
    print("###", 
        "day:", day, 
        "daily_balance:", daily_balance, "daily_fcr", daily_fcr_revenue, "daily_profit:", daily_profit, 
        "yearly_balance", yearly_balance, "yearly_fcr", yearly_fcr_revenue,  "yearly_profit", yearly_profit)
