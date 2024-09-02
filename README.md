# Дипломный проект профессии «Python-разработчик: расширенный курс»

## [Описание проекта](https://github.com/IvanTimofeev89/python-final-diplom)

### Задача
* Создать и настроить проект по автоматизации закупок в розничной сети. Проработать модели данных, импорт товаров, API views
### Развертывание проекта
* Указать значения переменных окружения, необходимых для оправки почтовый уведомлений, в файле .env: EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
* Команда для запуска docker compose up

### Реализованный функционал
* API сервис автоматизации закупок согласно спецификации
* Импорт товаров
* Отправка накладной на email администратора
* Отправка заказа на email клиента
* Административна панель


### Дополнительная информация:
* Внедрена система мониторинга Sentry
* Административная панель улучшена с помощью библиотеки Django JET Reboot
* [Документация по запросам в PostMan](https://documenter.getpostman.com/view/28416434/2sA3e5dnbk)
* В качестве альтернативы PostMan API реализована в Swagger (drf spectacular)
* Степень покрытия тестами - 56%
* Представление по загрузке yaml файла с информацией про продукции вынесена в отдельную Celery задачу
* Реализовано развертывание веб-сервера Nginx
* Для удобства тестирования и проверки добавлена команда создания супер пользователя, выполняющаяся при развертывании проект. Почтовы адрес и пароль суперпользователь указывается в файле .env
* Изменить тип пользователя на "shop" может только администратор через админпанель. Предполагается, что перед выдачей роли "магазин" администратор/менеджер проводит дополнительную проверку юридической документации магазина.
* В Postman добавлен дополнительный запрос на импорт товаров от лица второго магазина.
* При размещении нового заказа ему устанавливается статус "placed". Пользователь и администратор получают почтовое уведомление о размещении заказа. Предполагается, что администратор/менеджер проверяет корректность данных в заказе и через админпанель меняет статус заказа на "confirmed". Пользователь получит почтовое уведомление об изменении статуса заказа и автоматически изменится количество товара на остатках у магазина
