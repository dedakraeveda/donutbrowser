# Release gate — EXE и ZIP отдельно

## Текущий статус

Этот файл — checklist сопровождающего, а не протокол успешной проверки. Факты по конкретному EXE/ZIP находятся во внешнем VERIFICATION.md. Новый комплект собирается из чистого source snapshot и включает локальный CBrowser. Старый application-only Donut NSIS не является таким комплектом: он не содержит engine. Инструкции для клиентов не устанавливают generic secret/MCP bridge автоматически.

## Разрешение владельца — получено28.10.2026

Владелец подтвердил право на форк от разработчика и уточнил, что используемый CBrowser давно не равен Cloak. Упаковка существующего локального engine разрешена, см. AUTHORIZED_FORK.md. Не блокировать по одному совпадению версии с другими Chromium-based продуктами и не заменять requested embedded engine онлайн-загрузкой.

Выбран **CBrowser 1.33** (~536MiB). Техническое cache/build соответствие сохранено в корневом `146_Cl.txt`; не путать номер форка с Chromium protocol version. SHA256 chrome.dll: `ed7009a70d76fa4da222a5b37c34012d77fcc04092ef8df5fb572062940fa4dd`. Отдельную legacy151 линию не включать автоматически.

## Состав после закрытия блокера

- Native Donut browser manager и его обязательные sidecars.
- Один явно выбранный CBrowser engine, все DLL/resources/locales и license/NOTICE; не только chrome.exe.
- Portable entrypoint с разрешением engine относительно собственной папки, без D:/projects paths. Portable marker/data roots должны реально работать; запуск raw binary мимо launcher не должен читать старые профили/настройки.
- EXE installer и ZIP из одного проверенного payload. Installer не обновляет установленный личный Donut скрыто. Новый install location/data root, отдельные shortcuts и no-admin режим по возможности.
- Full matching AGPL source с модификациями, build/install scripts и dependency locks, либо сопровождающий source archive. Старый candidate binary и более новый source tree не считать matching release.
- START_HERE, technology attribution/наши дополнения, инструкции multi-agent, конфигурационные шаблоны без токенов. Явно отметить, где client adapter реально поставлен, а где дана инструкция.
- SHA256 manifest и внешний hash каждого EXE/ZIP, source revision и diff snapshot provenance.

## Что исключить

`.git`, node_modules, target, .next, старые releases, рабочий cache user data, браузерные profiles, cookies/storage, OAuth/session files, `.env`/непроверенные machine config, DPAPI/vault dumps, proxy credentials, browser-control leases, downloads/screenshots/logs/артефакты пользователя. Binary distribution включать только allowlist payload. Источники отбирать отдельно; personal paths/config не включать в source archive.

## Проверка перед release

1. Свободное место C и target drive до/между/после stages. TEMP/TMP/cache/build profiles на проверенном D workspace; минимум20GiB C для необязательных записей туда. Ниже10GiB остановить disk-growing C jobs.
2. Без изменения live установки — source-matching build; не запускать auto-update, не вызывать installer поверх личного приложения.
3. Стандартные format/lint/unit gates и соответствующие native E2E из AGENTS/update runbook. Не замалчивать недоступные suites/секреты/падения; release gate закрыт только подтверждёнными checks.
4. Native startup/settings/MCP integration/browser lifecycle tests в новом isolated data root. Учитывать application single-instance lock: не закрывать действующий manager владельца ради теста.
5. Реальный unpack/EXE install в новую папку с пробелами; verification payload hashes; никаких source-machine paths, CBrowser launch without installed Python/Node, WebView2 prerequisite clearly stated.
6. Новый browser profile, loopback CDP; benign fixture navigate/read/fill/click/postcondition. Не личный профиль. Verify isolation, fresh IDs/tokens, no imported owner data.
7. Реальный MCP initialize/tools/list; page_id multi-tab если заявлен; first-client smoke. Матрица других клиентов по официальным docs не равна их live проверке.
8. Uninstall/rollback только binaries, созданные задачей. Сохранить user state; не blanket-delete профили/credentials и не убивать чужие процессы.
9. Dashboard/wiki update с точными hashes и verification evidence. После sync проверить shortcut и final artifact existence. Git без add/commit/restore/reset: только read-only команды, если отдельно не разрешены.
