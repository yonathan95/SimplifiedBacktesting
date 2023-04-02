import pandas as pd
from backtest import Backtest
from strategies import RandomStrategy
from summary import Summary, plot_data

from utils import adjust_types


def main():
    data = pd.read_csv("/root/backtest/data/btcusdtperp.csv")
    data = adjust_types(data)
    b = Backtest(data, commission=0.0002, balance=10000, strategy=RandomStrategy())
    trading_data = b.backtest()
    summary = Summary(trading_data)
    summary.print_results()
    plot_data(trading_data)


if __name__ == "__main__":
    main()
