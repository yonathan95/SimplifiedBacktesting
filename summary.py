from math import sqrt
import pandas as pd
import numpy as np
import plotly.express as px

from utils import adjust_types

import seaborn as sns

from matplotlib import pyplot as plt
from simple_colors import red


class Summary:
    def __init__(self, data=None):
        self.max_balance_drowdown = None
        self.max_drawdown = None
        self.returns_std = None
        self.total_return = None
        self.sharpe = None
        self.downside_deviation = None
        self.sortino = None
        self.best_trade = None
        self.worst_trade = None
        self.calmar_ratio = None
        self.positive_trades = None
        self.positive_trading_days = None
        if type(data) != str:
            self.init(data)
        else:
            self.init_from_csv(data)

    def print_results(self):
        print(red("Total return:", "bold"), f"{self.total_return}%")
        print(red("Sharpe:", "bold"), f"{self.sharpe}%")
        print(red("Sortino:", "bold"), f"{self.sortino}%")
        print(red("Max balance drawdown:", "bold"), f"{self.max_balance_drowdown}%")
        print(red("Max drawdown:", "bold"), f"{self.max_drawdown}%")
        print(red("Returns std:", "bold"), f"{self.returns_std}%")
        print(red("Downside deviation:", "bold"), f"{self.downside_deviation}%")
        print(red("Best trade:", "bold"), f"{self.best_trade}%")
        print(red("Worst trade:", "bold"), f"{self.worst_trade}%")
        print(red("Positive trades:", "bold"), f"{self.positive_trades}%")
        print(red("Positive trading days:", "bold"), f"{self.positive_trading_days}%")

    def init_from_csv(self, csv_path):
        data = pd.read_csv(csv_path)
        data = adjust_types(data)
        self.init(data)

    def init(self, data):
        # max_balance_drowdown
        min_balance = min(data["Balance"])
        initial_balance = data["Balance"].iloc[0]
        self.max_balance_drowdown = round(
            (1 - (min_balance / initial_balance)) * 100, 3
        )

        # returns_std, convert to a series
        daily_returns_series = data[["Return rate with comm"]].iloc[:, 0]

        # max drawdown
        cumulative_max = daily_returns_series.cummax()
        drawdown = cumulative_max - daily_returns_series
        self.max_drawdown = round(drawdown.max() * 100, 3)

        # resample by day to get daily return
        daily_returns_series = daily_returns_series.resample("24H").sum()
        returns_std = daily_returns_series.std() * 100
        self.returns_std = round(returns_std, 3)

        # total_return
        end_balance = data["Balance"].iloc[-1]
        total_return = ((end_balance - initial_balance) / initial_balance) * 100
        self.total_return = round(total_return, 3)

        # sharpe ratio = total return percentage / standard deviation * sqrt(num of trading days)
        self.sharpe = round(
            total_return / (returns_std * sqrt(len(daily_returns_series))), 3
        )

        # downside deviation
        # remove positive returns
        negative_returns_std = (
            daily_returns_series.apply(lambda x: x if x < 0 else np.nan).dropna()
        ).std() / sqrt(len(daily_returns_series))
        self.downside_deviation = round(negative_returns_std * 100, 3)

        # sortino - same as sharpe but using downside deviation instead of regular std
        self.sortino = round(total_return / negative_returns_std, 3)

        # best and worse trade
        self.best_trade = round(max(data["Return rate with comm"].fillna(0)) * 100, 3)
        self.worst_trade = round(min(data["Return rate with comm"].fillna(0)) * 100, 3)

        # Percentage of positive trades
        trades = data["Return rate with comm"].dropna()
        profitable_trades = trades.apply(lambda x: x if x > 0 else np.nan).dropna()
        self.positive_trades = round((len(profitable_trades) / len(trades)) * 100, 3)

        # profitable_days
        profitable_days = daily_returns_series.apply(
            lambda x: x if x > 0 else np.nan
        ).dropna()
        self.positive_trading_days = round(
            (len(profitable_days) / len(daily_returns_series)) * 100, 3
        )


def plot_data(df):
    fig = px.line(df, x=df.index, y="Open", title="Protfolio size over time")
    fig.add_scatter(x=df.index, y=df["Pos"], mode="lines")
    fig.show()

    fig = px.line(
        df, x=df.index, y="Balance", title="Protfolio size over time", render_mode="SVG"
    )
    fig.show()

    fig = px.line(
        df, x=df.index, y="Minimal balance", title="Minimal balance over time"
    )
    fig.show()

    fig = px.box(df, y="Return rate")
    fig.show()

    sns.displot(df["Return rate"], rug=True, kind="kde")
    plt.show()


def main():
    path = "detailed_summaries/l&s-btc-fl25000000-sl50000000-rand3095.csv"
    df = pd.read_csv(path)
    summary = Summary(path)
    print(summary)
    plot_data(df)


if __name__ == "__main__":

    main()
