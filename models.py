from abc import ABCMeta, abstractmethod
import pandas as pd
from enum import Enum


class OrderType(Enum):
    OPEN_LONG = 1
    OPEN_SHORT = 2
    CLOSE_LONG = 3
    CLOSE_SHORT = 4


class PositionSide(Enum):
    LONG = 1
    SHORT = 2


class BrokerInstruction:
    def __init__(self, order_type: OrderType, price: float):
        self.order_type = order_type
        self.price = price


class Position:
    def __init__(self, qty: float, price: float, side: PositionSide):
        self.qty = qty
        self.price = price
        self.side = side
        self.low = price
        self.high = price


class Strategy(metaclass=ABCMeta):
    @abstractmethod
    def enter_position(self, data: pd.DataFrame) -> BrokerInstruction:
        raise NotImplementedError

    @abstractmethod
    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        raise NotImplementedError


class OutOfMoneyException(Exception):
    pass
