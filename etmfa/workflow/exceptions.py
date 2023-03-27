class InvalidWorkFlow(Exception):
    def __init__(self, name, input_connector, output_connector, *args):
        self.name = name
        self.input_connector = input_connector
        self.output_connector = output_connector
        super().__init__(args)

    def __str__(self):
        return f'{self.name} is not a valid workflow .{self.output_connector} and {self.input_connector} are not compatible '

class WorkFlowMissing(Exception):
    def __init__(self,name,*args):
        self.name=name
        super().__init__(args)

    def __str__(self):
        return f'{self.name} workflow does not exist '

class WorkFlowParamMissing(Exception):
    def __init__(self,name,*args):
        self.name=name
        super().__init__(args)

    def __str__(self):
        return f'Service name missing from workflow {self.name} '


class ReplyMsgException(Exception):
    def __init__(self, name, *args):
        self.name = name
        super().__init__(args)

    def __str__(self):
        return f'Unable to run message que, Reason: {self.name} '


class SendExceptionMessages(Exception):
    def __init__(self, name, *args):
        self.name = name
        super().__init__(args)

    def __str__(self):
        return f'{self.name}'