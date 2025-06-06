# Diploma
## Модельная задча
![изображение](https://github.com/user-attachments/assets/ba4327b6-f0f8-445a-b664-b15ff64f12a0)
Тонкие линии-дороги
Линии,выделенные жирным-общественный транспорт
## Зависимости
* Docker. [Установка](https://docs.google.com/presentation/d/1yGKtsHyUtIIPKTCl6uX8gAWbbg8GP3wHRRTO5XufZsM/edit?slide=id.g9a43d8b6c4_0_31#slide=id.g9a43d8b6c4_0_31)
* Python. Библиотеки: [osmiter(1.3.1)](https://pypi.org/project/osmiter/), [neo4j(5.28.1) ](https://pypi.org/project/neo4j/)
## Запуск
### Запуск neo4j с помощью docker: 
docker run -p 7474:7474 -p 7687:7687 --env NEO4J_AUTH="none" neo4j:5.26
<p>Web-интерфейс: http://localhost:7474/
<p>Логин: neo4j </p>
<p>Пароль: password</p>
  
### Запуск программы:
python3 main.py
