class ContractStore(metaclass=MethodBoundSingleton):
    """
    Some desciption
    """

    ADD_DATA = {"VVV": True}
    _contracts: dict[DocId, sbis.Record]
    _linked: dict[DocId, DocId | sbis.Record]
    _history: dict[DocId, list[DocId | None]]

    def __init__(self):
        """
        Initialize
        """
        self.clear()

    def clear(self):
        """
        Foo
        """
        self._contracts = {}
        self._linked = {}
        self._history = defaultdict(list)

    def get_contract(self, contract_id: DocId) -> bool:
        """
        Some desciption

        :param contract_id: 
        :returns: 

        """
        if contract_id not in self._contracts:
            self._contracts[contract_id] = load()
        return self._contracts[contract_id]
