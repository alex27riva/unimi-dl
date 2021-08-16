from unimi_dl.platform.ariel import Course
import unittest
from ..platform import Ariel
import os

class TestAriel(unittest.TestCase):
#    def __init__(self, methodName: str) -> None:
#        super().__init__(methodName=methodName)
    def setUp(self) -> None:
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        if username == None:
            raise EnvironmentError("No Username provided")

        if password == None:
            raise EnvironmentError("No Password provided")

        self.courses = []
        self.instance = Ariel(email=username, password=password)
        return super().setUp()

    def tearDown(self) -> None:
        self.instance.session.close()
        return super().tearDown()


    def test_create(self):
        assert(isinstance(self.instance, Ariel))

    def test_getcourses(self):
        ariel = self.instance

        self.courses = ariel.get_courses()
        for course in self.courses:
            assert(isinstance(course, Course))

    def test_course_getAttachments(self):
        ariel = self.instance
        
        courses = ariel.get_courses()
        course = courses[0]
        for section_name in course.getAvailableSections():
            print(section_name)
            assert(isinstance(section_name, str))
            assert(section_name != "")
            attachments = course.getSectionAttachments(section_name)
            for attachment in attachments:
                attachment.download("./")

    def test_ariel_course_create(self) -> None:
        
        pass

if __name__ == '__main__':
    unittest.main()
