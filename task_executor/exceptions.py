class TaskError(Exception):
    """Exception raised for errors when a Task is called.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="tag or content can not be null"):
        self.message = message
        super().__init__(self.message)

class TaskLogError(Exception):
    """Exception raised for errors when a TaskLog is called.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="task or status can not be null, status has to be a valid"):
        self.message = message
        super().__init__(self.message)