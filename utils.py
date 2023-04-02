from datetime import datetime as datetime


def adjust_types(data):
    data = data.astype(
        {
            "Open time": str,
            "Close time": str,
            "Open": float,
            "High": float,
            "Low": float,
            "Close": float,
            "Volume": float,
            "Quote asset volume": float,
            "Number of trades": float,
            "Taker buy volume": float,
            "Taker buy quote asset volume": float,
        }
    )
    data["Open time"] = data["Open time"].apply(
        lambda x: add_zero(x) if x.split(" ")[1][1] == ":" else x
    )
    data["Open time"] = data["Open time"].apply(
        lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
    )
    data.index = data["Open time"]
    return data


def add_zero(st):
    """
    :param st: a string with datetime
    :return: the same string with "0" before the hour if needed
    """
    splited = st.split(" ")
    return splited[0] + " 0" + splited[1]
