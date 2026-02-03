class Foo:
    """
    Foo
    """
    def currency_rate(self, exchange_info: ExchangeInfo, _filter: Record, record: Record) -> Decimal:
        """
        FofFoFOoFoOF FO Ofo FoFO oF oFO
            fdsfsdf  fsdfsdfs sdfsdfsdsdf sdffdssdf

        :param exchange_info:
        :param _filter:
        :param record:
        :returns:

        """
        if not exchange_info.currency:
            return Decimal(1)

        currency_rate = self._calc_currency_value(exchange_info, _filter, record)
        return Decimal(str(currency_rate)) if currency_rate else currency_rate