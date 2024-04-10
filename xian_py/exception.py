class XianException(Exception):
    def __init__(self, ex: Exception):
        super().__init__(str(ex))

        self.ex_name = type(ex).__name__
        self.ex_msg = str(ex)
        self.ex = ex
