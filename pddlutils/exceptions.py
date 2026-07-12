from pddl.exceptions import PDDLError


class PDDLLogicError(PDDLError):
    """Raised for PDDL error regarding logic of PDDL operations."""

    def __init__(self, message: str = "Logic Error"):
        """Initialize the PDDL logic exception."""
        self.message = message
        super().__init__(self.message)
