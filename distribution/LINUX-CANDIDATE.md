# Donut Agent Kit1.33 — Linux upstream146 compatibility candidate

Это комплект для локальной проверки: **наш Donut/launcher/профили/сеть/MCP + официальный неизменённый Linux-бинарник CloakBrowser146**. Это не пересобранный нами Chromium core: GitHub-source тег содержит только wrapper, см. docs/UPSTREAM-146-AUDIT.md. Происхождение движка и checksum находятся в ENGINE-PROVENANCE.json; upstream licenses сохранены в cbrowser/upstream-notices. Номер1.33 — нашего интеграционного комплекта, не подмена технической версии движка.

## Запуск

1. Ubuntu26.04 x64/glibc2.43, GTK3/WebKitGTK4.1, Python3.10+ и системные библиотеки Chromium, включая libnss3/libnspr4. Это не universalAppImage и не проверенный Debian/Astra/ARM build.
2. Полностью распакуй tar.gz в новую writable-папку. Проверь внешний SHA256.json, затем `./Donut-Agent-Kit verify --json`. Личные данные/профили/token владельца не включены.
3. Из графической пользовательской X11/Wayland-сессии: `./Donut-Agent-Kit preflight --json`, `./Donut-Agent-Kit plan --json`, `./Donut-Agent-Kit launch --json`. Не запускать browser отroot и не отключать sandbox глобально.
4. Данные этой копии — state/. Установленный личный Donut не обновляется. Токены и вход в сайты пользователь задаёт сам локально, не через чат/argv.
5. Новый отдельный CBrowser-profile для каждого агента; MCP в Settings→Integrations. docs/CLIENTS.md и AGENT-GUIDE.md содержат правила для разных клиентов. NativeMCP — широкий административный каталог, не read-only sandbox; не auto-approve всё.

## Что наше

Менеджер/Tauri UI, локальная политика обновлений, путь и lifecycle CBrowser, профиль/seed, routing worker, proxy→GeoIP/locale/timezone/coordinates, WebRTC settings, nativeMCP/REST и page_id, portablelauncher/manifests/docs. Устранена зависимость standaloneCBrowser API/MCP от Wayfern acceptance marker; сам Wayfern по-прежнему проверяет свои условия перед запуском. Linux-адаптер безопасно распознаёт flattenedargv по точному профильному SingletonLockPID и ожидаемому executable, а не по одному совпадению строки.

## Проверка

На новом профиле под непривилегированным Linuxпользователем проверены nativeDonut через официальный WebKitWebDriver, MCPinitialize/list81tools, запуск engine, точная вкладка/page_id, ввод/клик/чтение результата локальной формы, navigator.webdriver=false. Это не тест всех сайтов/утечек/антибот-систем и не macOSпроверка. Детальный VERIFICATION.md рядом с архивом.

Сеть нужна для сайтов и probeреального выхода; публичнаяGeoLite2data с MaxMindnotice приложена. Оригинальные engineбинарники и их лицензия отдельно от MITwrapper/AGPLDonut. Подтверждение владельца права на его существующий fork не следует путать с автоматической MITлицензией на любую новую стороннюю поставку. Этот candidate не опубликован вGitHubReleases и не заявляется самостоятельной нашей C++реализацией.

Откат: закрыть только эту копию, убрать её MCPconnector. state не удаляется автоматически. Предыдущие Windows и Linux app-only артефакты сохранены; никаких сбросов личного профиля или глобальных proxy/лицензионных настроек.
