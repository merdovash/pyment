"""
case
"""


class _Collector(metaclass=TransactionBoundSingleton):
    """
    _Collector
    """

    name = "paybill.doc_changed.event"

    def __init__(self):
        """
        Initialize
        """
        self.docs: dict[DocId, Decimal] = defaultdict(Decimal)

    def _add_link_data(self, _doc: DocId, _link: ILinkBuilder, /):
        pass

    def add_link(self, link: ILink):
        """
        Извлечет из связи данные для уведомления

        :param link: 
        :type link: ILink

        """
        pass

    def execute(self):
        """
        Опубликует события по всем документам, по которым изменился статус оплаты
        """
        pass


class UiNotification(ILinkOperationsHandler):
    """
    UiNotification
    """

    @ignorable()
    def process(self):
        """Отправит изменения в специальный коллектор
        :return:
        """
        pass
