# Основа Donut fork и наши дополнения

## Компоненты

| Слой | Основа | Назначение |
| --- | --- | --- |
| Desktop manager | Donut Browser (`zhom/donutbrowser`), AGPL-3.0 | локальные профили, сеть, lifecycle, integrations |
| Native приложение | Tauri 2, Rust | процессы, хранилища, REST/MCP/CDP, sidecars |
| Интерфейс | Next.js / React / TypeScript | UI управления профилями и интеграциями |
| CBrowser | наш локальный fork **CBrowser 1.33** (техническая версия — корневой `146_Cl.txt`) | реальный browser engine, отдельный user-data на профиль |
| Другой engine | Wayfern | отдельные entitlement/engine границы; не подмена CBrowser |
| Page automation | native Donut MCP либо официальный Playwright MCP через CDP | управление существующими Donut-owned страницами |
| Сеть | donut-proxy и Xray-core sidecars при нужной конфигурации | маршрутизация, прокси/VPN/VLESS; не облачный сервис quite |
| MCP-клиенты | Codex, Claude Code, Cursor, Cline и другие совместимые локальные клиенты | discovery и вызов tools |

Слово «наша» относится к интеграции и изменениям fork, не к авторству Chromium, Donut, Playwright, Xray или их криптографии. CBrowser wrapper0.5.8 и Playwright в старой `.local/cbrowser/python` — отдельный диагностический Python runtime. Самому Tauri-приложению для запуска browser EXE не нужен Python.

## Изменения нашего Donut fork

По текущему source tree (`AUTHORIZED_FORK.md`, `CBROWSER_SESSIONS.md`, Rust modules):

- интеграция CBrowser в lifecycle Donut (serialized engine id `cloak`), собственный профиль и детерминированный fingerprint seed;
- поиск локального browser binary, machine-local override через `BROWSER_BINARY_PATH`, выбор engine без скрытой миграции профиля;
- собственные локальные entitlement policy границы; это не выпуск облачных токенов/подписок и не разрешение обойти проверки внешнего engine;
- ручные app/browser executable updates; отдельная политика обновления non-executable GeoIP/DNS данных;
- proxy-derived timezone/locale/coordinates и WebRTC exit IP, CDP geolocation supervisor; известные ограничения отражены в CBROWSER_SESSIONS.md;
- поддержка native `list_tabs` и явного `page_id` в page tools (требуется реально собранный binary с этими изменениями);
- изолированные data roots и portable state, source E2E harness и тесты.

Это характеристика исходников. Установленная версия и сохранённый release binary не обязательно включают все более поздние правки. Версия `0.29.6+authorized.7` без хеша/даты сама по себе не доказывает идентичность сборки.

## Что добавлено для переносимого Agent Kit

- Небольшой Windows entrypoint на C#/.NET Framework: локальные capabilities/status/preflight/plan/launch/verify, JSON-конверт, проверка manifest, отдельные data/cache/TEMP/WebView2 roots. Использует штатный CreateProcessW без наследования stdio handles, чтобы GUI-процесс не блокировал JSON-команду coding-агента.
- Чистый source snapshot без `.env`, accounts и user state; новый application identifier `com.donutbrowser.agentkit`, отдельный EXE basename, без обновления личной установки Donut.
- Offline payload с полным существующим CBrowser и совпадающим по build tag donut-proxy; исходники Donut и packaging scripts внутри source ZIP. Для proxy использована release opt-level3 сборка без final thin-LTO из-за linker cache issue; это не упрощённый proxy.
- Fresh local defaults вместо старого onboarding, ожидающего Wayfern download; существующий конфиг не меняется. Новый профиль/аккаунт заранее не создаётся.
- Публичная GeoLite2 City data с MaxMind attribution для холодного запуска CBrowser. Это не браузерная история/кеш владельца; собственная база пользователя не перезаписывается.
- NSIS setup и portable ZIP из одного allowlisted payload, uninstall известных shipped files без удаления state, отдельные агентские инструкции/клиентская матрица и tests.

## Что НЕ является частью generic-комплекта автоматически

Политики `browser_control` в Pi реализует отдельный проект `pi-auth-browser`: leases, Pi Tasks pool, proxy preflight, standard/owner/autopilot guards, secret redaction, protected Agent Browser accelerator. Сам native Donut MCP не предоставляет этот слой. Документация для Codex/Cursor не устанавливает им Pi extension и не создаёт equivalent enforcement.

Профили, cookies, OAuth и proxy credentials владельца, Windows vault/DPAPI, machine-local IDs, installed account bindings и личные browser state не должны входить в distributable.

## Лицензии и разрешение владельца

Donut source имеет AGPL-3.0 (корневой LICENSE). При передаче производного binary нужно предоставить соответствующие исходники с нашими изменениями, build/install scripts и notices; нельзя выдавать старый EXE вместе с произвольным новым source snapshot за matching source.

28.10.2026 владелец подтвердил полученное от разработчика право на форк и сборку существующего локального CBrowser: «это далеко не cloak уже давно». Подтверждение зафиксировано в AUTHORIZED_FORK.md. В комплект входит **этот локальный CBrowser fork**, не заново скачанная поставка CloakHQ. Одинаковый Chromium version number не доказывает тождество бинарников и не меняет разрешение владельца.

Предыдущее предположение агента, что одного номера Chromium достаточно для блокировки упаковки как чужого binary, было ошибочным и снято после уточнения владельца. Полный комплект содержит browser engine; никакой незаметной замены на online bootstrap нет. Сохраняются upstream license/NOTICE и границы внешних сервисов. Разрешение на локальный fork не создаёт Donut/Wayfern cloud accounts, entitlements или права на посторонние данные.

## Sources

1. Donut upstream: https://github.com/zhom/donutbrowser ; local source LICENSE/AUTHORIZED_FORK.md/DUAL_ENGINE.md/CBROWSER_SESSIONS.md.
2. Разрешение локального CBrowser fork: подтверждение владельца28.10.2026, записанное в AUTHORIZED_FORK.md. Не смешивать с условиями заново скачиваемых сторонних сборок.
3. Official Playwright MCP: https://github.com/microsoft/playwright-mcp .
