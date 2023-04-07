


class GenericException(Exception):
    def __init__(self,msg,_id=None):
        self.id = _id
        self.msg=msg

    def __str__(self):
        return f'Failure :  {self.msg} for id {self.id}'