from unittest import TestCase

from init import ResourceManager
from tests.testing import MyTestCase


class TestResourceManager(MyTestCase):
    def setUp(self):
        super().setUp()
        self.o = ResourceManager()

    def test_init(self):
        pass