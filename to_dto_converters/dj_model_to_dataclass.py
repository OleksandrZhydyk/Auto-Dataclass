import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type, ForwardRef, List, get_origin, Union
from django.db.models.manager import Manager
from django.db.models import Model


T = Type["T"]


class ToDTOConverter(ABC):
    @abstractmethod
    def to_dto(self, data, dc: dataclass):
        pass


class FromOrmToDataclass(ToDTOConverter):

    def __init__(self):
        self._is_recursive = False
        self._current_dataclass = None
        self._future_dataclasses = None

    def to_dto(self, data: Model, dc: dataclass, is_recursive: bool = False,
               future_dataclasses: List[dataclass] = None) -> dataclass:
        self._is_recursive = is_recursive
        checked_dc = self._check_dataclass_arg(dc)
        self._current_dataclass = checked_dc
        self._future_dataclasses = self._check_future_dataclasses_arg(future_dataclasses)
        checked_data = self._is_data_dj_model_type(data)
        return self._to_dataclass_obj(checked_data, checked_dc)

    def _to_dataclass_obj(self, data: Model, dc: dataclass) -> dataclass:
        obj_for_dataclass = {}
        for field in dataclasses.fields(dc):
            if self._is_field_name_exists_in_data(data, field.name):

                field_data = getattr(data, field.name)
                origin_type, is_list = self._get_origin_field_type(field.type)

                if is_list and dataclasses.is_dataclass(origin_type) and field_data is not None:
                    obj_for_dataclass[field.name] = self._get_list_of_dataclass_objects(
                        field_data, origin_type
                    )
                elif dataclasses.is_dataclass(origin_type) and field_data is not None:
                    obj_for_dataclass[field.name] = self._get_dataclass_object(
                        field_data, origin_type
                    )
                else:
                    obj_for_dataclass[field.name] = field_data
        return dc(**obj_for_dataclass)

    @staticmethod
    def _is_field_name_exists_in_data(data: Model, field_name: str) -> bool | None:
        if hasattr(data, field_name):
            return True
        raise AttributeError(
            f"Field name '{field_name}' doesn't exist in {data}"
        )

    def _get_origin_field_type(self, field_type):
        is_list = False
        if get_origin(field_type) is Union:
            field_type = field_type.__args__[0]
        if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
            field_type = field_type.__args__[0]
            is_list = True
        if isinstance(field_type, ForwardRef):
            field_type = field_type.__forward_arg__
            field_type = self._get_future_object_type(field_type)
        if isinstance(field_type, str):
            field_type = self._get_future_object_type(field_type)
        return field_type, is_list

    def _get_dataclass_object(self, field_data: Model, field_type: type) -> dataclass:
        return self._to_dataclass_obj(field_data, field_type)

    def _get_list_of_dataclass_objects(
        self, field_data: Manager, field_type: T
    ) -> List[dataclass]:
        values_lst = []
        for orm_obj in field_data.all():
            values_lst.append(self._to_dataclass_obj(orm_obj, field_type))
        return values_lst

    def _get_future_object_type(self, obj_type: str) -> dataclass:
        if self._is_recursive:
            return self._current_dataclass
        if self._future_dataclasses:
            for dc in self._future_dataclasses:
                if dc.__name__ == obj_type:
                    return dc
            raise TypeError(
                f"The 'future_dataclasses' arguments must be defined for future reference '{obj_type}'."
            )
        raise TypeError(
            f"The dataclass {self._current_dataclass} has recursive or future relation"
            f" that was not defined. Please define argument 'is_recursive' for recursive relation or "
            f"'future_dataclasses' for future relations"
        )

    @staticmethod
    def _check_dataclass_arg(dc: dataclass) -> dataclass:
        if dataclasses.is_dataclass(dc):
            return dc
        raise TypeError(f"The 'dc' arg should be dataclass type, not {type(dc)} type")

    @staticmethod
    def _check_future_dataclasses_arg(future_dataclasses: List[dataclass] | None) -> List[dataclass] | None:
        if future_dataclasses is None:
            return future_dataclasses
        if not isinstance(future_dataclasses, list):
            raise TypeError(
                f"The 'future_dataclasses' arguments should be a list of 'dataclass' classes or "
                f"None type, not {type(future_dataclasses)}."
            )
        for dc in future_dataclasses:
            if not dataclasses.is_dataclass(dc):
                raise TypeError(
                    f"The 'future_dataclasses' arguments should be a list of 'dataclass' classes. "
                    f"Received {dc} with type {type(dc)}."
                )
        return future_dataclasses

    @staticmethod
    def _is_data_dj_model_type(data: Model):
        if isinstance(data, Model):
            return data
        raise TypeError(
            f"Data must be a django.db.models.Model type. Instead, received '{type(data)}'"
        )
