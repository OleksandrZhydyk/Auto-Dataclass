import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass, is_dataclass
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
        self._future_dataclasses = []

    def to_dto(self, data: Model, dc: dataclass,
               future_dataclasses: List[dataclass] = None) -> dataclass:
        checked_dc = self._check_dataclass_arg(dc)
        self._future_dataclasses.append(checked_dc)
        self._check_future_dataclasses_arg(future_dataclasses)
        checked_data = self._is_data_dj_model_type(data)
        return self._to_dataclass_obj(checked_data, checked_dc)

    def _to_dataclass_obj(self, data: Model, dc: dataclass) -> dataclass:
        obj_for_dataclass = {}
        for field in dataclasses.fields(dc):
            if self._is_field_name_exists_in_data(data, field.name):

                field_data = getattr(data, field.name)
                origin_type, is_list = self._get_origin_field_type(field.type)

                if is_list and is_dataclass(origin_type) and field_data is not None:
                    obj_for_dataclass[field.name] = self._get_list_of_dataclass_objects(
                        field_data, origin_type
                    )
                elif is_dataclass(origin_type) and field_data is not None:
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
        try:
            for orm_obj in field_data.all():
                values_lst.append(self._to_dataclass_obj(orm_obj, field_type))
        except AttributeError:
            raise TypeError(f"The {field_data} is not iterable, but specified type is List[{field_type}]")
        return values_lst

    def _get_future_object_type(self, obj_type: str) -> dataclass:
        if self._future_dataclasses:
            for dc in self._future_dataclasses:
                if dc.__name__ == obj_type:
                    return dc
            raise TypeError(
                f"The 'future_dataclasses' arguments must be defined for future reference '{obj_type}'."
            )

    @staticmethod
    def _check_dataclass_arg(dc: dataclass) -> dataclass:
        if dataclasses.is_dataclass(dc):
            return dc
        raise TypeError(f"The 'dc' arg should be dataclass type, not {type(dc)} type")

    def _check_future_dataclasses_arg(self, future_dataclasses: List[dataclass]) -> None:
        if future_dataclasses is None:
            return
        if not isinstance(future_dataclasses, list):
            raise TypeError(
                f"The 'future_dataclasses' arguments should be a list of 'dataclass' classes or "
                f"None type, not {type(future_dataclasses)}."
            )
        for dc in future_dataclasses:
            if not is_dataclass(dc):
                raise TypeError(
                    f"The 'future_dataclasses' arguments should be a list of 'dataclass' classes. "
                    f"Received {dc} with type {type(dc)}."
                )
            self._future_dataclasses.append(dc)

    @staticmethod
    def _is_data_dj_model_type(data: Model):
        if isinstance(data, Model):
            return data
        raise TypeError(
            f"Data must be a django.db.models.Model type. Instead, received '{type(data)}'"
        )
