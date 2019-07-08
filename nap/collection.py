from collections import UserList


class ListWithAttributes(UserList):
    def __init__(self, list_vals, extra_data=None):
        self.extra_data = extra_data if extra_data else {}

        super().__init__(list_vals)
