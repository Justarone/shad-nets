# Лабораторная работа - исследование разных механизмов TLS через анализ дампов трафика. Настройка TLS-сервисов.

Необходимо написать простой tls-client, используя TLS-API любой доступной вам реализации. Клиент должен поддерживать работу по TLS 1.2 и TLS 1.3 (версия протокола определяется пользователем) с использованием шифронаборов (ciphersuite), также задаваемых пользователем.
Клиент должен уметь выполнить tls-handshake, сделать http-запрос к веб-серверу (адрес сервера и документ также указываются пользователем), а после получения ответа – выполнить graceful shutdown. Также клиент должен уметь проверить сертификат сервера (построить цепочку и верифицировать ее).
Когда у вас будет готова реализация такого клиента, нужно сделать подключение по TLS 1.2 и TLS  1.3 к любому публичному серверу, сохранить Wireshark-log этого соединения и приложить к нему премастер-ключ/эфемеральный ключ для расшифрования лога (обращаю внимание – перед выбором библиотеки, реализующей API TLS, проверьте, что сможете получить эти значения – многие реализации TLS это сделать не дадут!).

Язык реализации не важен.

За реализацию дополнительных tls-механизмов (двусторонняя аутентификация, PHA и прочее) - будут плюшки.

Что нужно сдать?
- Исходный код с инструкцией по сборке.
- Описание решения.
- Два лога Wireshark (1.2 и 1.3).
- Ключи для расшифрования логов. 

Срок сдачи: 24 мая 2024 года.
Вопросы: @msk_dosimetrist, vasnikolaev@yandex-team.ru.
