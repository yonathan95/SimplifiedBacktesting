from typing import Dict
from models import (
    OutOfMoneyException,
    Strategy,
    BrokerInstruction,
    OrderType,
    PositionSide,
    Position,
)
import pandas as pd

from strategies import RandomStrategy
from summary import Summary, plot_data
from utils import adjust_types

POSITION_MARGIN = 2000


class Backtest:
    def __init__(
        self,
        data: pd.DataFrame,
        commission: float,
        balance: int,
        strategy: Strategy,
        leverage: int = 1.0,
        window_size: int = 100,
        buy_percentage: float = 0.05,
    ):
        self.data = data
        self.commission = commission
        self.balance = balance
        self.wallet = {"USDT": balance, "BTC": 0, "loaned_USDT": 0, "loaned_BTC": 0}
        self.strategy = strategy
        self.leverage = leverage
        self.window_size = window_size
        self.buy_percentage = buy_percentage

    def __repr__(self):
        return "<Backtest " + str(self) + ">"

    def broker_action(self, qty: float, price: float, instruction: BrokerInstruction):

        usdt_balance = (
            self.wallet["USDT"] - qty * price * self.commission
        )  # usdt after commission
        btc_balance = self.wallet["BTC"]
        loaned_usdt = self.wallet["loaned_USDT"]
        loaned_btc = self.wallet["loaned_BTC"]

        if instruction.order_type == OrderType.OPEN_LONG:
            self.wallet["USDT"] = usdt_balance - (qty / self.leverage) * price
            self.wallet["BTC"] = btc_balance + qty
            self.wallet["loaned_USDT"] = (
                loaned_usdt + (qty - (qty / self.leverage)) * price
            )
            return Position(qty, price, PositionSide.LONG)

        elif instruction.order_type == OrderType.OPEN_SHORT:
            self.wallet["USDT"] = usdt_balance + qty * price
            self.wallet["BTC"] = btc_balance - (qty / self.leverage)
            self.wallet["loaned_BTC"] = loaned_btc + qty - (qty / self.leverage)
            return Position(qty, price, PositionSide.SHORT)

        elif instruction.order_type == OrderType.CLOSE_LONG:
            self.wallet["USDT"] = usdt_balance + qty * price - loaned_usdt
            self.wallet["BTC"] = btc_balance - qty
            self.wallet["loaned_USDT"] = 0
            return None

        else:
            self.wallet["USDT"] = usdt_balance - qty * price
            self.wallet["BTC"] = btc_balance + (qty / self.leverage)
            self.wallet["loaned_BTC"] = 0
            return None

    def update_balance(self, btc_open, btc_high, btc_low):
        self.balance = (
            self.wallet["USDT"]
            + self.wallet["BTC"] * btc_open
            - self.wallet["loaned_USDT"]
            - self.wallet["loaned_BTC"] * btc_open
        )

        balance_high = (
            self.wallet["USDT"]
            + self.wallet["BTC"] * btc_high
            - self.wallet["loaned_USDT"]
            - self.wallet["loaned_BTC"] * btc_high
        )

        balance_low = (
            self.wallet["USDT"]
            + self.wallet["BTC"] * btc_low
            - self.wallet["loaned_USDT"]
            - self.wallet["loaned_BTC"] * btc_low
        )

        if balance_low <= 0 or balance_high <= 0:
            raise OutOfMoneyException

        return min(balance_low, balance_high)

    def calc_return(self, position: Position, close_price: float):
        open_price = position.price

        if position.side == PositionSide.SHORT:
            return_rate = (open_price - close_price) / open_price
        else:
            return_rate = (close_price - open_price) / open_price

        return return_rate * self.leverage

    def calc_return_with_comm(self, position: Position, close_price: float):
        open_price = position.price
        commission = position.price * self.commission + close_price * self.commission

        if position.side == PositionSide.SHORT:
            return_rate = (open_price - close_price - commission) / open_price
        else:
            return_rate = (close_price - open_price - commission) / open_price

        return return_rate * self.leverage

    def calc_price(
        self, instructions: BrokerInstruction, candle: Dict, change_size: int = 2.0
    ):
        curr_close = candle["Close"]
        curr_open = candle["Open"]

        slippage_rate = ((curr_close - curr_open) / curr_open) / change_size

        price = instructions.price

        if instructions.order_type in [OrderType.OPEN_LONG, OrderType.CLOSE_SHORT]:
            return max(price + price * slippage_rate, price)

        else:
            return min(price - price * slippage_rate, price)

    def backtest(self):

        position: Position = None
        data = self.data.copy(deep=True)
        for i in range(self.window_size, len(self.data) + 1):

            curr_data = data[i - self.window_size : i]
            past_data = curr_data[:-1]
            curr_row_idx = data.index[i - 1]
            curr_candle = curr_data[-1:].to_dict(orient="records")[0]

            minimal_balance = self.update_balance(
                curr_candle["Open"], curr_candle["High"], curr_candle["Low"]
            )
            data.loc[curr_row_idx, "Balance"] = self.balance
            data.loc[curr_row_idx, "Minimal balance"] = minimal_balance
            data.loc[curr_row_idx, "USDT"] = self.wallet["USDT"]
            data.loc[curr_row_idx, "BTC"] = self.wallet["BTC"]
            data.loc[curr_row_idx, "Loaned USDT"] = self.wallet["loaned_USDT"]
            data.loc[curr_row_idx, "Loaned BTC"] = self.wallet["loaned_BTC"]

            if position is None:
                data.loc[curr_row_idx, "Pos"] = curr_candle["Open"]
                instruction: BrokerInstruction = self.strategy.enter_position(
                    data=past_data
                )

                if instruction is not None:
                    data.loc[curr_row_idx, "Actions"] = instruction.order_type

                    actual_price = self.calc_price(instruction, curr_candle)
                    qty = (
                        self.balance * self.buy_percentage / actual_price
                    ) * self.leverage

                    position = self.broker_action(qty, actual_price, instruction)

            else:

                if position.side == PositionSide.SHORT:
                    curr_data.loc[curr_row_idx, "Pos"] = (
                        curr_candle["Open"] - POSITION_MARGIN
                    )
                else:
                    curr_data.loc[curr_row_idx, "Pos"] = (
                        curr_candle["Open"] + POSITION_MARGIN
                    )

                if i == len(self.data):
                    last_close = list(curr_data["Close"])[-1]
                    if position.side == PositionSide.LONG:
                        instruction = BrokerInstruction(
                            OrderType.CLOSE_LONG, last_close
                        )
                    else:
                        instruction = BrokerInstruction(
                            OrderType.CLOSE_SHORT, last_close
                        )
                else:
                    instruction = self.strategy.exit_position(
                        data=past_data, position=position
                    )

                if instruction is not None:
                    data.loc[curr_row_idx, "Actions"] = 0  # position closed

                    actual_price = self.calc_price(instruction, curr_candle)

                    return_rate = self.calc_return(position, actual_price)
                    return_rate_comm = self.calc_return_with_comm(
                        position, actual_price
                    )

                    data.loc[curr_row_idx, "Return rate"] = return_rate
                    data.loc[curr_row_idx, "Return rate with comm"] = return_rate_comm
                    position = self.broker_action(
                        position.qty, actual_price, instruction
                    )

        trading_data = data[self.window_size :]
        trading_data.to_csv(f"results/{'test_name'}.csv")
        return trading_data
