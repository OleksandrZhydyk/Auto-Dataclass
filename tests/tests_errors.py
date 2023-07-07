from dataclasses import dataclass
from typing import List
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from django.db.models import Model, QuerySet

from auto_dataclass.dj_model_to_dataclass import FromOrmToDataclass
from auto_dataclass.exceptions import ConversionError


class TestErrorToDTOFunc(TestCase):
    @dataclass
    class TestDataclass:
        id: int
        name: str

    def setUp(self) -> None:
        self.converter = FromOrmToDataclass()

    def test_error_to_dto_incorrect_data_type(self) -> None:
        queryset = Mock(spec=QuerySet)

        with self.assertRaises(ConversionError):
            self.converter.to_dto({"test": "dict"}, self.TestDataclass)

        with self.assertRaises(ConversionError):
            self.converter.to_dto(queryset, self.TestDataclass)

    def test_error_to_dto_incorrect_dataclass(self) -> None:
        class IsNotDataclass:
            id: int
            name: str

        mock_model = Mock(spec=Model)
        mock_model.id = 1
        mock_model.name = "first"

        with self.assertRaises(ConversionError) as cm:
            self.converter.to_dto(mock_model, IsNotDataclass)
        self.assertEqual(
            f"The 'dc' arg should be dataclass type, not {type(IsNotDataclass)} type",
            str(cm.exception)
        )

    def test_error_to_dto_incorrect_dataclass_field_name(self) -> None:

        InnerTestDataclass = self.TestDataclass

        @dataclass
        class OuterTestDataclass:
            non_existed_field_name: int
            dc: List[InnerTestDataclass]

        mock_model = Mock(spec=Model)
        mock_related_manager = MagicMock()
        mock_related_manager.all.return_value = self.get_list_db_model_objects()
        mock_model.id = 1
        mock_model.dc = mock_related_manager

        with self.assertRaises(ConversionError) as cm:
            self.converter.to_dto(mock_model, OuterTestDataclass)
        self.assertEqual(
            f"Field name 'non_existed_field_name' doesn't exist in {mock_model}",
            str(cm.exception)
        )

    def test_error_to_dto_incorrect_future_dataclasses_arg_type(self):
        @dataclass
        class RecursiveTestDataclass:
            id: int
            dc: 'FutureTestDataclass'

        @dataclass
        class FutureTestDataclass:
            id: int

        outer_mock_model = Mock(spec=Model)
        inner_mock_model = Mock(spec=Model)
        inner_mock_model.id = 2
        inner_mock_model.dc = None
        outer_mock_model.id = 1
        outer_mock_model.dc = inner_mock_model

        future_dataclass = "future_dataclasses"

        with self.assertRaises(ConversionError) as cm:
            self.converter.to_dto(
                outer_mock_model,
                RecursiveTestDataclass,
                future_dataclasses=future_dataclass
            )
        self.assertEqual(
            f"The 'future_dataclasses' arguments should be a list of 'dataclass' classes or "
            f"None type, not {type(future_dataclass)}.", str(cm.exception)
        )

    def test_error_incorrect_future_dataclasses_arg_type_value(self):
        @dataclass
        class RecursiveTestDataclass:
            id: int
            dc: 'FutureTestDataclass'

        @dataclass
        class FutureTestDataclass:
            id: int

        outer_mock_model = Mock(spec=Model)
        inner_mock_model = Mock(spec=Model)
        inner_mock_model.id = 2
        inner_mock_model.dc = None
        outer_mock_model.id = 1
        outer_mock_model.dc = inner_mock_model

        future_dataclass = "future_dataclasses"

        with self.assertRaises(ConversionError) as cm:
            self.converter.to_dto(
                outer_mock_model,
                RecursiveTestDataclass,
                future_dataclasses=[future_dataclass]
            )
        self.assertEqual(
            "The 'future_dataclasses' arguments should be a list of 'dataclass' classes. "
            f"Received {future_dataclass} with type {type(future_dataclass)}.", str(cm.exception)
        )

    def test_error_to_dto_incorrect_future_dataclasses_arg_value(self):
        @dataclass
        class RecursiveTestDataclass:
            id: int
            dc: 'FutureTestDataclass'

        class FutureTestClass:
            id: int

        outer_mock_model = Mock(spec=Model)
        inner_mock_model = Mock(spec=Model)
        inner_mock_model.id = 2
        inner_mock_model.dc = None
        outer_mock_model.id = 1
        outer_mock_model.dc = inner_mock_model

        with self.assertRaises(ConversionError) as cm:
            self.converter.to_dto(
                outer_mock_model,
                RecursiveTestDataclass,
                future_dataclasses=[FutureTestClass]
            )
        self.assertEqual(
            "The 'future_dataclasses' arguments should be a list of 'dataclass' classes. "
            f"Received {FutureTestClass} with type {type(FutureTestClass)}.", str(cm.exception)
        )

    def test_error_missed_future_dataclasses_arg(self):
        @dataclass
        class RecursiveTestDataclass:
            id: int
            dc: 'FutureTestDataclass'

        @dataclass
        class FutureTestDataclass:
            id: int

        outer_mock_model = Mock(spec=Model)
        inner_mock_model = Mock(spec=Model)
        inner_mock_model.id = 2
        inner_mock_model.dc = None
        outer_mock_model.id = 1
        outer_mock_model.dc = inner_mock_model

        with self.assertRaises(ConversionError) as cm:
            self.converter.to_dto(
                outer_mock_model,
                RecursiveTestDataclass
            )
        self.assertEqual(
            f"The 'future_dataclasses' argument must be defined for future reference 'FutureTestDataclass'.",
            str(cm.exception)
        )

    def test_error_to_dto_incorrect_field_type(self) -> None:

        InnerTestDataclass = self.TestDataclass

        @dataclass
        class OuterTestDataclass:
            id: int
            dc: List[InnerTestDataclass]

        mock_model = Mock(spec=Model)
        mock_model.id = 1
        mock_model.dc = self.get_list_db_model_objects()[0]

        with self.assertRaises(ConversionError) as cm:
            self.converter.to_dto(mock_model, OuterTestDataclass)
        self.assertEqual(
            f"The {mock_model.dc} is not iterable, but specified type is List[{InnerTestDataclass}]",
            str(cm.exception)
        )

    @staticmethod
    def get_list_db_model_objects():
        model_instance_1 = Mock(spec=Model)
        model_instance_1.id = 1
        model_instance_1.name = "first"
        model_instance_2 = Mock(spec=Model)
        model_instance_2.id = 2
        model_instance_2.name = "second"

        return [model_instance_1, model_instance_2]
