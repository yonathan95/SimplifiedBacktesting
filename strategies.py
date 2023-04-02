from models import Strategy, BrokerInstruction, OrderType, PositionSide, Position
import random
import pandas as pd


class RandomStrategy(Strategy):
    """
    Opens a position with probability buy_p, decides whether long or short with p = 0.5
    Closes position with probability sell_p
    """

    def __init__(self, buy_p=0.1, sell_p=0.005):
        super().__init__()
        self.buy_p = buy_p
        self.sell_p = sell_p

    def enter_position(self, data: pd.DataFrame) -> BrokerInstruction:
        last_close = data["Close"].iloc[-1]
        if self.buy_p > random.random():
            if random.random() >= 0.5:
                return BrokerInstruction(OrderType.OPEN_LONG, last_close)
            else:
                return BrokerInstruction(OrderType.OPEN_SHORT, last_close)

    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        last_close = data["Close"].iloc[-1]
        if self.sell_p > random.random():
            if position.side == PositionSide.LONG:
                return BrokerInstruction(OrderType.CLOSE_LONG, last_close)
            else:
                return BrokerInstruction(OrderType.CLOSE_SHORT, last_close)


class BuyAndHold(Strategy):
    def enter_position(self, data: pd.DataFrame):
        last_close = data["Close"].iloc[-1]
        return BrokerInstruction(OrderType.OPEN_LONG, last_close)

    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        return
