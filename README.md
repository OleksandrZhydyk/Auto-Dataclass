## Auto dataclass
![ci_badge](https://github.com/OleksandrZhydyk/Auto-Dataclass/actions/workflows/tests.yml/badge.svg)
[![Downloads](https://static.pepy.tech/badge/auto_dataclass)](https://pepy.tech/project/auto_dataclass)

AutoDataclass is a simple package that helps easy to map data into DataTransferObject for transporting that data between system layers.
The package uses specified Dataclass structure for retrieving data and creating DTO.
Currently, supported Django model object to Dataclass object conversion.


### Installation
```shell
pip install auto_dataclass
```

### Quickstart

```shell
# Django models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=1000)
    
class Photo(models.Model):
    product = models.ForeignKey(Product, related_name="photos",
                                on_delete=models.CASCADE)
    image = models.ImageField(blank=True)
```

Define your Dataclasses that describe retrieved data structure from DB.
```shell
# dto.py
@dataclass(frozen=True)
class PhotoDataclass:
    id: int
    image: str

@dataclass(frozen=True)
class ProductDataclass:
    id: int
    name: str
    description: str
    photos: List[ProductDataclass] = field(default_factory=list)
```
Create `Converter` instance and call `to_dto` method with passed data from the query and previously defined Dataclass.
```shell
# repository.py
from auto_dataclass.dj_model_to_dataclass import FromOrmToDataclass

from dto import ProductDataclass
from models import Product

# Creating Converter instance
converter = FromOrmToDataclass()

def get_product(product_id: int) -> ProductDataclass:
    product_model_instance = Product.objects \
                    .prefetch_related('photos') \
                    .get(pk=product_id) 
    # Converting Django model object from the query to DTO.     
    retrun converter.to_dto(product_model_instance, ProductDataclass)
```

### Recursive Django model relation

If your data has a recursive relation you can also map them with the same way.

```shell
# Django models.py
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=128)
    parent = models.ForeignKey(
        "Category", related_name="sub_categories", null=True, blank=True, on_delete=models.CASCADE
    )
```

```shell
# dto.py
@dataclass
class CategoriesDTO:
    id: int
    name: str
    sub_categories: List['CategoriesDTO'] = field(default_factory=list)
```

```shell
# repository.py
from itertools import repeat
from auto_dataclass.dj_model_to_dataclass import FromOrmToDataclass

from models import Category
from dto import CategoriesDTO

converter = FromOrmToDataclass()

def get_categories(self) -> Iterable[CategoriesDTO]:
    category_model_instances = Category.objects.filter(parent__isnull=True)
    return map(converter.to_dto, category_model_instances, repeat(CategoriesDTO))
```

### Future Dataclass data types

Example of mapping future relation in Dataclasses structure.

```shell
# dto.py

@dataclass
class Dataclass:
    id: int
    dc: Optional['FutureDataclass']
    
@dataclass
class FutureDataclass:
    id: int
    name: str
```

To handle this you just need to pass a future Dataclasses as a next arguments.
```shell
from auto_dataclass.dj_model_to_dataclass import FromOrmToDataclass
from dto import Dataclass, FutureDataclass

converter = FromOrmToDataclass()

dataclass_with_future_relation = converter.to_dto(
    django_data_model,
    Dataclass,
    FutureDataclass
)
```
