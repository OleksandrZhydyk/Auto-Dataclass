from dataclasses import dataclass
from typing import List
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from django.db.models import Model

from auto_dataclass.dj_model_to_dataclass import FromOrmToDataclass


class TestToDataclassObjFunc(TestCase):

    @dataclass
    class TestDataclass:
        id: int
        name: str

    def setUp(self) -> None:
        self.converter = FromOrmToDataclass()

    def test__to_dto_python_types(self) -> None:
        model = self.get_db_model_object()
        result = self.converter.to_dto(model, self.TestDataclass)

        self.assertEqual(result, self.TestDataclass(id=1, name="first"))

    def test_to_dto_list_of_python_types(self) -> None:
        @dataclass
        class TestDataclass:
            id: int
            name: List[str]

        mock_model_with_list = Mock(spec=Model)
        mock_model_with_list.id = 1
        mock_model_with_list.name = ["first_name", "last_name"]

        result = self.converter.to_dto(mock_model_with_list, TestDataclass)

        self.assertIsInstance(result, TestDataclass)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name[1], "last_name")

    def test__to_dto_db_related_object(self) -> None:
        InnerTestDataclass = self.TestDataclass

        @dataclass
        class OuterTestDataclass:
            dc: InnerTestDataclass

        mock_model = Mock(spec=Model)
        mock_model.dc = self.get_db_model_object()
        result = self.converter.to_dto(mock_model, OuterTestDataclass)

        self.assertIsInstance(result, OuterTestDataclass)
        self.assertEqual(result.dc, InnerTestDataclass(id=1, name="first"))

    def test__to_dto_list_db_related_objects(self) -> None:
        InnerTestDataclass = self.TestDataclass

        @dataclass
        class OuterTestDataclass:
            dc: List[InnerTestDataclass]

        mock_model = Mock(spec=Model)
        mock_related_manager = MagicMock()
        mock_related_manager.all.return_value = self.get_list_db_model_objects()
        mock_model.dc = mock_related_manager
        result = self.converter.to_dto(mock_model, OuterTestDataclass)

        self.assertIsInstance(result, OuterTestDataclass)
        self.assertIsInstance(result.dc, list)
        self.assertEqual(result.dc[1], InnerTestDataclass(id=2, name="second"))

    def test__to_dto_list_db_related_objects_or_none(self) -> None:
        InnerTestDataclass = self.TestDataclass

        @dataclass
        class OuterTestDataclass:
            dc: List[InnerTestDataclass] | None

        mock_model = Mock(spec=Model)
        mock_model.dc = None
        result = self.converter.to_dto(mock_model, OuterTestDataclass)

        self.assertIsInstance(result, OuterTestDataclass)
        self.assertEqual(result.dc, None)

    @staticmethod
    def get_db_model_object():
        model = Mock(spec=Model)
        model.id = 1
        model.name = "first"
        return model

    @staticmethod
    def get_list_db_model_objects():
        model_instance_1 = Mock(spec=Model)
        model_instance_1.id = 1
        model_instance_1.name = "first"
        model_instance_2 = Mock(spec=Model)
        model_instance_2.id = 2
        model_instance_2.name = "second"

        return [model_instance_1, model_instance_2]
