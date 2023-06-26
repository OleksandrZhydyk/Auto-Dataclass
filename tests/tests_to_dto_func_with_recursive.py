from typing import List, Optional
from unittest import TestCase
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock
from django.db.models import Model

from auto_dataclass.dj_model_to_dataclass import FromOrmToDataclass


class TestToDTOFuncRecursiveRelations(TestCase):
    @dataclass
    class TestDataclass:
        id: int
        name: str

    def setUp(self) -> None:
        self.converter = FromOrmToDataclass()

    def test_to_dto_recursive_relation(self) -> None:
        @dataclass
        class RecursiveTestDataclass:
            id: int
            dc: 'RecursiveTestDataclass'

        outer_mock_model = Mock(spec=Model)
        inner_mock_model = Mock(spec=Model)
        inner_mock_model.id = 2
        inner_mock_model.dc = None
        outer_mock_model.id = 1
        outer_mock_model.dc = inner_mock_model

        result = self.converter.to_dto(
            outer_mock_model,
            RecursiveTestDataclass,
            is_recursive=True
        )

        self.assertIsInstance(result, RecursiveTestDataclass)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.dc, RecursiveTestDataclass(id=2, dc=None))

    def test_to_dto_list_recursive_relation(self) -> None:
        @dataclass
        class RecursiveTestDataclass:
            id: int
            dc: List['RecursiveTestDataclass'] | None

        inner_mock_model = Mock(spec=Model)
        inner_mock_model.id = 2
        inner_mock_model.dc = None

        mock_related_manager = MagicMock()
        mock_related_manager.all.return_value = [inner_mock_model, inner_mock_model]

        outer_mock_model = Mock(spec=Model)
        outer_mock_model.id = 1
        outer_mock_model.dc = mock_related_manager

        result = self.converter.to_dto(
            outer_mock_model,
            RecursiveTestDataclass,
            is_recursive=True)

        self.assertIsInstance(result, RecursiveTestDataclass)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.dc[1], RecursiveTestDataclass(id=2, dc=None))

    def test_to_dto_list_future_relations(self) -> None:
        @dataclass
        class RecursiveTestDataclass:
            id: int
            dc: List['RecursiveTestDataclass'] | None
            double_dc: Optional['RecursiveDataclass']

        @dataclass
        class RecursiveDataclass:
            id: int
            name: str

        inner_mock_model = Mock(spec=Model)
        inner_mock_model.id = 2
        inner_mock_model.dc = None
        inner_mock_model.double_dc = None

        mock_related_manager = MagicMock()
        mock_related_manager.all.return_value = [inner_mock_model, inner_mock_model]

        recursive_mock_model = Mock(spec=Model)
        recursive_mock_model.id = 3
        recursive_mock_model.name = "name"

        outer_mock_model = Mock(spec=Model)
        outer_mock_model.id = 1
        outer_mock_model.dc = mock_related_manager
        outer_mock_model.double_dc = recursive_mock_model

        result = self.converter.to_dto(
            outer_mock_model,
            RecursiveTestDataclass,
            future_dataclasses=[RecursiveDataclass, RecursiveTestDataclass]
        )

        self.assertIsInstance(result, RecursiveTestDataclass)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.dc[1], RecursiveTestDataclass(id=2, dc=None, double_dc=None))
        self.assertEqual(result.double_dc, RecursiveDataclass(id=3, name="name"))
