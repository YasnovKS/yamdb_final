[![Yamdb_final](https://github.com/YasnovKS/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)](https://github.com/YasnovKS/yamdb_final/actions/workflows/yamdb_workflow.yml)
# YaMDb - API для сбора отзывов пользователей на произведения
Итоговый командный проект модуля *"API: интерфейс взаимодействия программ"* курса "Python-разработчик плюс" от Яндекс.Практикум в котором необходимо было разработать API для собора отзывов на произведения.

## Технологии
* Django Rest Framework
* JWT based authorization (SimpleJWT)
* Python
* Git

## Как запустить проект на локальном компьютере
Инструкция ниже предусматривает, что у Ваш компьютер готов для работы с Docker.
1. Перейдите в директорию, в которой находится файл docker-compose.yaml (по умолчанию: /infra_sp2/infra);
2. В командной строке введите команду docker-compose up -d --build;
3. Для нормльной работы приложения необходимо выполнить миграции:
3.1. в командной строке введите "docker-compose exec web python manage.py migrate" (это создаст необходимые миграции);
3.2. зарегистрируйте суперюзера с помощью команды "docker-compose exec web python manage.py createsuperuser";
3.3. выполните сбор статики при помощи команды "docker-compose exec web python manage.py collectstatic --no-input"
После проведения этих операций приложение может быть открыто по адресу http://localhost/.

## Импортирование тестовых данных
Данные в csv формате можно импортировать в БД через manage.py команду `python3 manage.py importdata`

Перед тем как выполнить команду, необходимо
1. В `settings.py` указать путь к папке с тестовыми данными через переменную `TEST_DATA_DIR`
```Python
TEST_DATA_DIR = os.path.join(BASE_DIR, 'static', 'data')
```
2. Указать список моделей в `Reviews.management.commands.importdata`, для которых необходимо импортировать данные.
```Python
from Reviews.management.base import ImportDataBaseCommand
from Reviews.models import Category, Genre, GenreTitle, Title
from Users.models import User


class Command(ImportDataBaseCommand):
    models = (Category, Genre, Title, GenreTitle, User)
```

Порядок моделей важен, так как некоторые модели могут ссылаться на существующие записи в других моделях.

Имена файлов должны соответствовать именам моделей в snake case формате.
Команда преобразует имя модели из camel case в snake case и переводит буквы в нижней регистр.
Например, для модели `GenreTitle`, команда будет искать файл `genre_title.csv` в директории `TEST_DATA_DIR`

Данные должны быть в формате csv с заголовком на первой строке. Заголовки должны соответствовать именам полей модели.

```CSV
id,name,slug
1,Фильм,movie
2,Книга,book
3,Музыка,music
```

Если у модели есть поля ссылающиеся на другую модель (ForeignKey), то команда определит это, сделает запрос по id на ссылаемый объект и уже этот объект будет использован при создании.

```CSV
id,name,year,category
1,Побег из Шоушенка,1994,1
```

Заголовок `category` это поле в модели `Title`:

```Python
class Title(models.Model):
    #...
    category = models.ForeignKey(
        Category,
        related_name='categories',
        on_delete=models.SET_NULL,
        null=True,
    )
```

При добавлении записи в таблицу Title, команда сначала сделает запрос
```Python
obj = Category.objects.get(pk=1)
```
и затем выдаст команду:

```Python
Title.objects.get_or_create(...,category=obj,...)
```

Если таблица модели содержит id ссылаемого объекта, то необходимо добавить суффикс '_id' к наименованию заголовка.
В этом случае в запросе на создание будет использован id ссылаемого объекта напрямую.

```CSV
id,title_id,genre_id
1,1,1
```

Несмотря на то, что в модели GenreTitle поля genre и title имеют тип ForeignKey, создание объекта в таблице должно быть напрямую через id. Поэтому в csv выше добавлены суффиксы '_id'.

```Python
class GenreTitle(models.Model):
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)
```

В этом случае, команда не будет делать запрос в `Genre` и `Title`, а напрямую выполнит:

```Python
GenreTitle.objects.get_or_create(title_id='1',genre_id='1')
```


## Авторы
* Василиса Немоляева
* Кирилл Яснов
* Сергей Ли


##MIT License

Copyright (c) 2022 Practicum Students

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
