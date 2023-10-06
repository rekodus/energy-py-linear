"""Example of using a battery for economic and carbon optimization."""
# python battery_unax3.py | grep "###"
import energypylinear as epl
import pandas as pd

# number of cars per month
no_chargers = 300
kwh_per_car = 30
power_mw = 11 * no_chargers / 1000
capacity_mw = no_chargers * kwh_per_car / 1000
final_charge_mwh = no_chargers * kwh_per_car / 1000
efficiency = 0.9
wholesale_prices_mwh = { 2023:102.1, 2024:91.0,	2025:88.4, 2026:78.0, 2027:74.7, 2028:69.0, 2029:67.9, 2030:57.2}
use_fcr = True
fcr_n_prices_mwh = { 2023:55.9, 2024:53.3,	2025:48.5, 2026:37.1, 2027:	26.55, 2028: 18.21, 2029:14.4, 2030:12.0}
fcr_d_up_prices_mwh = { 2023:55.9, 2024:53.3,	2025:48.5, 2026:37.1, 2027:	26.55, 2028: 18.21, 2029:14.4, 2030:12.0}

fcr_acceptance_rate = 0.8
price_curve_file = 'marketdata.csv'

#  battery model
asset = epl.Battery(power_mw=power_mw, capacity_mwh=capacity_mw, efficiency=efficiency)

def simulate_year(year, label, df):
    batch_size = 24
    num_batches = len(df) // batch_size
    # print ("***", num_batches)

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
                daily_fcr_revenue += fcr_acceptance_rate * fcr_n_prices_mwh[year] * power_mw
        daily_profit = daily_balance + wholesale_prices_mwh[year] * final_charge_mwh + daily_fcr_revenue
        yearly_balance += daily_balance
        yearly_fcr_revenue += daily_fcr_revenue
        yearly_profit += daily_profit
    print("### year", year, "type", label, "yearly_balance", yearly_balance, "yearly_fcr", yearly_fcr_revenue,  "yearly_profit", yearly_profit)

#df = pd.read_csv('day_ahead.csv', header=None, names=['value'])
df_master = pd.read_csv(price_curve_file)
for year in range(2024,2031):
    for label in ['DA', 'ID']:
        df = df_master[df_master['Year'] == year][label]
        simulate_year(year, label, df)

