# Donut Agent Kit — Linux x86_64

## Статус этой поставки

**APP-ONLY: Linux-бинарник нашего CBrowser пока отсутствует.** Нативные Donut и donut-proxy собраны и не содержат Windows EXE. Это не полный эквивалент Windows-комплекта и не замена движка на Cloak/обычный Chromium. Номер форка остаётся **CBrowser1.33**; исходная техническая версия находится в корневом146_Cl.txt.

Полный комплект можно собрать тем же packaging script после получения настоящего Linux-бинарника нашего CBrowser от разработчика/владельца. До этого engineBundled=false, а launcher корректно останавливает обычный запуск с `linux-cbrowser-required`. Нет фиктивного engine или скрытой загрузки другого браузера.

## Поддерживаемая среда

Сборочная/проверочная платформа: **Ubuntu26.04 x86_64**, GTK3, WebKitGTK4.1, libsoup3. Python3.10+ нужен только локальному launcher, дополнительные Python-пакеты не нужны. Donut — нативный ELF, не Wine. Наличие Python не создаёт MCP-инструменты само по себе.

Артефакт динамически связан с Linux-библиотеками. Он не объявляется универсальным для Debian12/Ubuntu22.04/Astra и не включает GTK/WebKit. Для другой glibc/WebKit-среды нужен соответствующий нативный build/test, не случайная подмена .so. ARM64 этим выпуском не проверяется.

Обычно зависимости ставятся пакетами дистрибутива: `libwebkit2gtk-4.1-0`, `libgtk-3-0t64`, `libayatana-appindicator3-1`, `python3`. Названия проверяй под свою Ubuntu; не запускай apt на другом дистрибутиве вслепую. Нужна графическая X11/Wayland-сессия; root и безусловный `--no-sandbox` для обычного использования не рекомендуются.

## Распаковка и диагностика

Распакуй tar.gz в новую постоянную writable-папку, не в общий/cloud каталог и не поверх личного Donut. Сохрани executable bits. Проверяй внешний SHA256.json; MANIFEST.json контролирует файлы внутри пакета, не является подписью автора.

```sh
./Donut-Agent-Kit capabilities --json
./Donut-Agent-Kit status --json
./Donut-Agent-Kit verify --json
```

`verify` проверяет manifest, но не выдаёт отсутствие engine за успешное подключение. Для **этого app-only** пакета status возвращает engineBundled=false, enginePresent=false, пока владелец не укажет настоящий Linux CBrowser.

## Подключить собственный Linux CBrowser

Получить разрешённую Linux x64 сборку нашего форка с полным комплектом DLL/.so/resources/locales и приложенными notices. Не копировать Windows chrome.exe, чужие профили или cookies. После проверки источника и хешей владелец локально создаёт `state/launcher.local.json`:

```json
{
  "enginePath": "/absolute/path/to/your-linux-cbrowser/chrome"
}
```

Это **шаблон**, замени путь своим реальным файлом. Файл содержит путь, не токен. Launcher требует настоящий executable ELF и никогда сам не скачивает альтернативу. Для полноценной одинаковой с Windows геопривязки нужна публичная GeoLite2-City.mmdb в state/cache с её MaxMind notices/условиями, не приватный browser cache.

```sh
./Donut-Agent-Kit preflight --json
./Donut-Agent-Kit plan --json
./Donut-Agent-Kit launch --json
```

Launch использует только данный kit и отдельный state; не меняет установленный Donut. Учётные данные, код/2FA и MCP/REST token вводи сам в локальном UI. Далее docs/CLIENTS.md и docs/AGENT-GUIDE.md: отдельный профиль на агента, explicit profile UUID/page_id, loopback-only, snapshot→action→postcondition. Это широкий native MCP admin catalog, не узкий read-only gateway. Автоодобрение всего каталога не включать.

## Нативная пересборка сопровождающим

Из чистой копии source на Linux с Node/pnpm, Rust и Tauri prerequisite libraries:

```sh
pnpm install --frozen-lockfile
pnpm build
node src-tauri/download-xray.mjs --target x86_64-unknown-linux-gnu
export BUILD_TAG=0.29.6-authorized.7-kit1
export CARGO_BUILD_JOBS=1
cargo build --release --locked --manifest-path src-tauri/Cargo.toml --bin donut-proxy
cp src-tauri/target/release/donut-proxy src-tauri/binaries/donut-proxy-x86_64-unknown-linux-gnu
cargo build --release --locked --manifest-path src-tauri/Cargo.toml --bin donutbrowser
```

Если CARGO_TARGET_DIR задан отдельно, `cp` берёт binary оттуда. Полностью изолировать данные/TEMP/cache, сначала проверить физический диск WSL VHDX и свободное место; не писать тяжёлую сборку на системный Windows-диск. Упаковка полного комплекта требует `--engine-root`:

```sh
python3 distribution/build_linux.py --source . --native-outputs src-tauri/target/release --output /your/new/release-folder --engine-root /your/verified/linux-cbrowser
```

Пути — явные поля пользователя, не готовые результаты. Для честно ограниченной поставки вместо engine-root используется **`--app-only`**, что обязательно видно в имени архива и manifest. Без выбранного режима packager отказывает. Engine никогда не включать из приватного user-data, даже если там есть chrome.

## Что проверено

Подробный VERIFICATION.md рядом с конкретным tar.gz различает build, process/health, MCP и live engine smoke. Windows-тесты не являются Linux-тестами. Пока Linux engine не предоставлен, CBrowser launch/form/MCP page-control на Linux не могут считаться проверенными.

## Откат

Закрыть только этот kit, убрать добавленный connector из клиента. Папка state принадлежит пользователю и не удаляется автоматически; исходный tar.gz остаётся переносимым дистрибутивом. Настроенную папку с cookies/сессиями нельзя передавать другому человеку/ПК. Не менять system browser, proxy или чужую установку во время удаления.
