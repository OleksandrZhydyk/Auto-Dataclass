## Django ORM Model to DataClass object
Package that helps easy convert Django ORM models to DTO(Dataclass) object.


### Installation
```shell
pip install djangomodel-dataclass
```

### Quickstart

```shell
# models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(max_length=1000)
    
class Photo(models.Model):
    product = models.ForeignKey(Product, related_name="photos",
                                on_delete=models.CASCADE)
    image = models.ImageField(blank=True)
```

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

```shell
# repository.py
from converters.dj_model_to_dataclass import FromOrmToDataclass

from dto import ProductDataclass
from models import Product

converter = FromOrmToDataclass()

def get_product(product_id: int) -> ProductDataclass:
    product = Product.objects \
                    .prefetch_related('photos') \
                    .get(pk=product_id)      
    retrun converter.to_dto(product, ProductDataclass)
```

### Recursive Django model relation

```shell
# models.py
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
from converters.dj_model_to_dataclass import FromOrmToDataclass

from models import Category
from dto import ProductDataclass

converter = FromOrmToDataclass()

def get_categories(self) -> Iterable[CategoriesDTO]:
    categories = Category.objects.filter(parent__isnull=True)
    return map(converter.to_dto, categories, repeat(CategoriesDTO), repeat(is_recursive=True))
```