# Donut Agent Kit — начни здесь

**Donut Browser fork + наш локальный CBrowser 1.33 внутри**, Windows x64. Не требует исходной среды quite, Python, Node.js, Rust или Visual Studio на целевом ПК. Профили, cookies, токены и proxy владельца не включены. Интернет нужен только для сайтов, optional non-executable data refresh и настройки пользователя, не для скачивания вложенного browser engine.

## Два варианта одного комплекта

- **setup.exe** — обычная установка в выбранную папку и ярлык в меню Пуск.
- **windows-x64.zip** — распаковать в постоянную папку и пользоваться без установки.

Состав payload одинаковый. Это отдельный **Donut Agent Kit**, не обновление уже установленного Donut: отдельный application identifier и изолированный state. Две копии Agent Kit одновременно не запускать; обычный Donut владельца заменять/останавливать не нужно.

## Установка: 3 шага

1. Проверь SHA-256 EXE/ZIP по SHA256.json из доверенного источника. Для ZIP не запускай прямо из архива — распакуй полностью. Выбери постоянную writable-папку, желательно на D: или другом несистемном диске. Сам комплект занимает примерно0.7GiB после распаковки; оставь минимум2GiB для старта и существенно больше под профили/загрузки. На C: при остатке меньше20GiB launcher просит другой диск.
2. Запусти **`Donut Agent Kit.exe` в корне**, либо ярлык из меню Пуск. Не запускай отдельно `app/donutbrowser-kit.exe` или `cbrowser/chrome.exe`: entrypoint выбирает bundled engine и перенаправляет state/TEMP/WebView2 cache в папку комплекта. На Windows11 обычно уже есть Microsoft Edge WebView2 Runtime; если его нет — установи официальный Evergreen Runtime с https://developer.microsoft.com/microsoft-edge/webview2/ . В комплекте системный WebView2 не дублируется.
Старый upstream-мастер первого запуска, ожидающий загрузку Wayfern, в этом комплекте заменён этой инструкцией: launcher создаёт новые локальные defaults с `onboarding_completed=true` и путём вложенного CBrowser. Лицензии сохранены в комплекте. Существующие настройки пользователя он не меняет; никакие профили заранее не создаются.

3. В Donut создай **новый CBrowser profile**, например `Agent Tasks 1`. Войди в сайты самостоятельно. Не импортируй чужой user-data, cookies, vault или OAuth.

EXE установщика не подписан коммерческим Authenticode certificate. Не отключай антивирус/SmartScreen глобально: проверь источник, хеш и исходники. SHA-256 manifest — контроль целостности, не цифровая подпись автора.

## Где данные и настройки

- `app/` — Donut и sidecars.
- `cbrowser/` — полный локальный CBrowser 1.33, а не только chrome.exe.
- `146_Cl.txt` — исходная техническая версия Chromium для совместимости/cache. Номер нашего форка — **1.33**; бинарные version resources и протокол Chromium не подменяются.
- `assets/GeoLite2-City.mmdb` — публичная справочная GeoIP-база с MaxMind attribution; launcher копирует её в новый state/cache только если там ещё нет базы. Это не пользовательский кеш и не история браузера. Точность/свежесть не гарантируется; обновления non-executable данных остаются отдельной политикой Donut.
- `state/` — создаётся при первом запуске; data/cache/logs/TEMP/WebView2, новые профили, настройки и локальные секреты **этого** пользователя. Не пересылай эту папку.
- `docs/` — инструкции агентам, клиентам и описание состава.
- `licenses/` и LICENSE-Donut-AGPL-3.0.txt — notices/лицензии/разрешение владельца. Chromium dependency credits доступны также на `chrome://credits` в браузере.
- `Donut-Agent-Kit-source.zip` — source snapshot Donut и scripts, соответствующий этой сборке; node_modules/target/user state исключены. Исходники engine Chromium не выдаются за нашу разработку; отдельный локальный fork поставляется по подтверждённому владельцем разрешению разработчика.
- `MANIFEST.json` — хеши поставленных файлов. Пользовательские state-файлы в него не входят.

Это portable-local layout, но НЕ обещание переносить авторизованные профили между компьютерами. Windows vault/DPAPI/browser encryption могут привязывать данные к текущей машине. На другом ПК распакуй исходный ZIP и авторизуйся заново. Настроенную папку не передавать другому человеку; передавай оригинальный дистрибутив.

## Подключить агента

1. Прочитай `docs/AGENT-GUIDE.md`; различай native MCP и отдельный policy layer.
2. В Donut Settings → Integrations включи MCP и посмотри фактический loopback URL/port. REST включай только если выбранному адаптеру он нужен; токены у них разные.
3. MCP token вводи **сам непосредственно в локальные настройки/secret механизм клиента**. Не отправляй его агенту, в чат, Git или параметры команд. Предпочитай tokenless `/mcp` URL с отдельным auth header, а не URL с токеном.
4. Открой `docs/CLIENTS.md`: отдельные маршруты для Codex, Claude Code, Cursor, Cline, Pi и ограничения Claude Desktop. MCP-конфиг другого клиента не всегда совместим; native Pi browser_control автоматически не устанавливается.
5. Дай агенту прочитать корневой `AGENTS.md` и `docs/AGENT-GUIDE.md`. Выдели конкретный profile UUID, сайт и границы задачи. Сначала tools/list и один benign smoke, затем личные задачи.

**Native Donut MCP — широкий admin-каталог.** Он не является узким read-only gateway: включает удаление/import/export/cookies/управление профилями. Не включай auto-approve всего каталога. Для недоверенного агента нужен отдельный enforcing gateway; текстовая инструкция его не заменяет.

## Локальная CLI-диагностика без секретов

У entrypoint есть JSON-команды (в терминале из папки комплекта):

```text
"Donut Agent Kit.exe" capabilities --json
"Donut Agent Kit.exe" status --json
"Donut Agent Kit.exe" preflight --json
"Donut Agent Kit.exe" plan --json
"Donut Agent Kit.exe" verify --json
"Donut Agent Kit.exe" launch --json
```

В PowerShell перед quoted EXE нужен штатный оператор вызова `&`. `verify` проверяет payload hashes и отдельно возвращает running PIDs; **не** доказывает MCP connectivity. `launch` запускает только этот manager, проверяет process alive, не создаёт аккаунт/профиль и не входит на сайты. По двойному клику launcher работает без окна консоли. Диагностика не читает tokens/профили. Exit0 — запрос выполнен/локальная проверка прошла;2 — ожидаемая precondition rejection;1 — unexpected failure. Схема JSON включает ok/operation/contractVersion/result/evidence либо error.

## Если что-то не работает

- **payload-missing/hash-mismatch:** распакуй исходный доверенный ZIP в новую папку, проверь внешний SHA-256. Не отключай проверку и не заменяй один EXE неизвестным файлом.
- **system-disk-low:** перенеси НЕНАСТРОЕННЫЙ исходный комплект на другой диск и запусти там. Уже настроенные профили/vault не мигрируй автоматически; сначала backup/план.
- **another-kit-running:** используй окно уже запущенной копии или закрой её сам. Launcher не убивает процессы и не крадёт профили.
- **manager-exited/check-webview-runtime:** проверь официальный WebView2, наличие DLL/sidecars и права записи в выбранную папку. Логи только в state/logs; не отправляй их целиком без локальной проверки приватных данных.
- **MCP401:** сверяй именно MCP token/URL в local UI. Сохранённый конфиг не доказывает здоровье сервера. При ротации обнови только этот connector.
- **Нет tools/не виден localhost:** Donut должен работать на том же ПК, что MCP-клиент. Облачные агенты не видят твой127.0.0.1. Не открывай manager/CDP наружу и не отключай auth.
- **Не тот профиль/вкладка:** остановись, обнови список UUID/табов, выбери точный `page_id`. Не делай fallback на личный профиль.
- **CAPTCHA/OTP/site restriction:** решает пользователь, без обхода.

## Обновление и удаление

App/browser executable self-update в нашем fork выключен. Обновляй вручную из проверенного нового комплекта, с backup и согласованной миграцией своего state. Нельзя заменять engine, пока профили работают. GeoIP/DNS — отдельные non-executable данные, их политика описана в source AUTHORIZED_FORK/CBROWSER_SESSIONS.

Перед удалением закрой только Agent Kit. Uninstaller удаляет только известные поставленные файлы и свой ярлык/registry entry, **state оставляет**. Для ZIP закрой приложение и сначала сохрани нужные данные; удаление своих state/credentials — отдельное осознанное действие пользователя. Другой установленный Donut и его профили не затрагиваются.

Что использовано и что своё: **`docs/STACK.md`**. Точный smoke/ограничения конкретного выпуска смотри во внешнем VERIFICATION.md рядом с EXE/ZIP; не считай инструкцию доказательством теста всех IDE.
