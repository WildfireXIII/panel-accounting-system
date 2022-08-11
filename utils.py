def dollars(value: float, dollar_sign: bool = True) -> str:
    if dollar_sign:
        return "${:,.2f}".format(value)
    else:
        return "{:,.2f}".format(value)
