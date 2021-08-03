import unittest
from ..platform import Ariel
import os

class TestAriel(unittest.TestCase):
    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        assert(True)
        if username == None:
            username = ""

        if password == None:
            password = ""

        self.instance = Ariel(email=username, password=password)

    def test_create(self):
        assert(isinstance(self.instance, Ariel))

    def test_getcourses(self):
        ariel = self.instance
        ariel.get_courses()

if __name__ == '__main__':
    unittest.main()
