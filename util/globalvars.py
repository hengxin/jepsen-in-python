class GlobalVars:
    __clients = []
    __nemesis = None

    @classmethod
    def set_clients(cls, clients):
        cls.__clients = clients

    @classmethod
    def get_clients(cls):
        return cls.__clients

    @classmethod
    def set_nemesis(cls, nemesis):
        cls.__nemesis = nemesis

    @classmethod
    def get_nemesis(cls):
        return cls.__nemesis
