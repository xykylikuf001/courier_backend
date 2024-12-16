class PaymentError(Exception):
    def __init__(self, message, code=None):
        super(PaymentError, self).__init__(message, code)
        self.message = message
        self.code = code

    def __str__(self):
        return self.message


class GatewayError(IOError):
    pass
