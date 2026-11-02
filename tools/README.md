# Генерация и проверка

Все семь схем хранятся в `Task*/diagrams/*.puml`, экспорт — только PNG. Они используют стандартный PlantUML; внешние includes и сеть для генерации не требуются. ER/component diagrams используют встроенный Smetana; sequence/activity — нативный layout. C4-библиотека в других работах не изменяется.

Из корня проекта, с существующими Python, Java и PlantUML:

```sh
python3 FinUnion/tools/render_diagrams.py --java /path/to/java --jar /path/to/plantuml.jar
python3 FinUnion/tools/validate.py --source '/Users/alex-pash/Downloads/Sprint#6.docx'
```

`render_diagrams.py` сначала проверяет синтаксис, затем генерирует PNG. Java нужна и при наличии расширения VS Code; скрипт принимает явный путь и не меняет настройки редактора. Установка ПО или внешний render server не требуются, если runtime уже доступен.

`validate.py` использует Pillow: проверяет 25 обязательных Markdown-файлов, семь пар исходник/PNG, целостность PNG, локальные ссылки. Все тексты задания остаются Markdown. 
