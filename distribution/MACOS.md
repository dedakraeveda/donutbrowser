# Donut Agent Kit1.33 — macOS preparation

## Свежий движок — отдельная зависимость

После запроса на более свежую версию проверен currentupstream: GitHubStable155.0.8059.39.2-pro, документация также предлагает preview156. Они требуют официальный ключ даже в бесплатном режиме; локальный ключ в этойсессии не обнаружен. Поэтому текущий запуск CI — **app-only**, не подмена новогоengine на145/146. Для новогоengine нужны локальный дистрибутив/исходники разработчика либо официальный доступ; ключи не передаются вGit/CI/ZIP/чат. Подробнее: WINDOWS-NATIVE.md. Все наши доступные manager/profile/network/MCP изменения остаются в source; закрытые C++patches не считаются автоматически перенесёнными.

## Честный текущий статус

Подготовлены **nativeMac build script**, Swift `.app` entrypoint и ручной GitHubActions pipeline для AppleSilicon/Intel. В этой Windows/WSL-сессии **готовые `.app/.dmg` ещё НЕ собраны**, MacGUI и запуск Macengine не проверены. Наличие workflow не означает успешную сборку или нотариализацию.

Публичный CloakBrowser146 GitHub-tag содержит wrapper, не исходники C++engine, и **не содержит macOS146 assets**. Тот же wrapperпинит обе Macархитектуры на145.0.7632.109.2. Поэтому предусмотрены два явно обозначенных режима:
- `app-only`: наш nativeDonut + matchingproxy/Xray/Swiftlauncher, без browserengine;
- `upstream-legacy`: наша интеграция + **неизменённый upstreamMac145** с pinnedSHA, ENGINE-PROVENANCE и исходными notices. Это compatibilitycandidate, не наш source-rebuilt146core.

Форковый номер1.33 отделён от технической версии; корневой146_Cl.txt сохраняется, а Macengine145 явно указан в KIT.json/ENGINE-PROVENANCE и имени candidate. Подмена145 на146 и переписывание vendorбинарника не делаются.

## Где наши части

Donut/Tauri UI и локальныйpolicy/runtime, CBrowserresolver, профиль/seed/lifecycle, routing/proxy/GeoIP/locale/timezone/geolocation/WebRTC, MCP/REST и page_id, agentinstructions. Swiftentrypoint выбирает вложенный nativeengine, очищает наследованные Donut/browserenv, задаёт отдельный data/TEMP root и не наследует agentstdout. Пароли/OTP/токены не вводятся черезargv, конфиги не копируются с чужогоПК. Chromiumcore/58патчей изwrapperarchive получить нельзя, см.UPSTREAM-146-AUDIT.md.

## На своём Mac

Нужны Mac с XcodeSDK/command-line tools, Rust/rustup, Node24, pnpm по packageManagerрепозитория, Python3 с безопаснымtarfiledatafilter (3.12+). Цели:
- AppleSilicon: `aarch64-apple-darwin`;
- Intel: `x86_64-apple-darwin`.

Минимальныйdeploymenttarget нашегоentrypoint12.0. Это не обещание, что все upstreamengine/OSверсии уже протестированы. Для выпуска нужен реальныйMacsmoke.

```sh
python3 distribution/build_macos.py \
  --target aarch64-apple-darwin \
  --work /your/new/build-folder \
  --output /your/new/output-folder \
  --engine-mode app-only
```

Пути — пользовательские поля, не готоваяпапка. Для явно разрешённого upstreamMac145candidate заменить engine-mode наupstream-legacy. Script отказывает на Windows/Linux и не запускает macOS через фиктивныйcrossbuild. Перед стартом проверяет12GiB наdestinationvolume; используйте запас подcargo/pnpm/cache/engine/zip/dmg. Изолированныйsnapshot исключает .env/профили/секреты и sourceopener.envloader, appidentityотдельныйcom.donutbrowser.agentkit.

Выходы: `.app` внутриZIP, `.dmg`, matchingDonutSource tar.gz, SHA256.json. Криптографическая целостность: стандартныеSHA256/CryptoKit иcodesign, не самописнаякриптография. Подпись **ad-hoc**, неDeveloperID и неAppleNotarization. Нет приватныхAppleсертификатов/паролей/секретов из исходноймашины. Script проверяет codesign и launcherverify, но не объявляет GUI/website smoke пройденным.

## GitHub macOS runners

Файл `.github/workflows/agent-kit-macos.yml` запускается **только вручную** черезworkflow_dispatch. Двеархитектуры, read-onlyrepositorypermissions, no persisted checkoutcredentials, noGitHubReleasecreation, артефактыкандидаты хранятся7дней. Секреты/Applecredentials ненужны дляad-hoccandidate. Ничего не развёртывается на личномMac.

Workflow должен сначала попасть в разрешённую ветку GitHub: это публикация инструкции сборки, **не** публичный выпуск приложения. Владелец разрешил текущие task-scoped add/commit/push и manualbuild. Это не бессрочная Git-авторизация для следующих задач. До реального successfulrun нетdownloadlinkготовогоDMG.

## Использование собранного кандидата

1. ПроверитьSHA256 из доверенногобилда и notices. `.app` положить в writable/persistent location безперезаписи личногоDonut.
2. macOSGatekeeperможет блокировать ad-hoc/nonnotarizedapp: проверить источник/сборку и пользоваться штатным локальнымOpenAnywayпо политике владельца. **Не отключать Gatekeeper/SIP и не удалятьquarantine рекурсивно вслепую**.
3. Открыть `Donut Agent Kit.app`; stateсоздаётся в `~/Library/Application Support/DonutAgentKit`, не вчужомbrowserprofile. Этоткаталог нельзя пересылать какoriginalдистрибутив.
4. CLIдиагностика: `"/your/path/Donut Agent Kit.app/Contents/MacOS/DonutAgentKit" capabilities --json`, status/preflight/plan/verify/launch. App-onlyбездвижка честноостанавливаетсяmacos-engine-required.
5. ВключениеMCP/REST/userlogin/OTP — только самомувlocalUI или черезотдельныйпроверенныйsecrethelper. NativeMCPширокийadmintoolcatalog, неautoapproveвсё. Профильнакаждогоагента; явныйUUID/page_id; snapshot/action/postcondition. docs/CLIENTS иAGENT-GUIDE.
6. ДляfullMacrelease проверить coldstart, enginearchitecture, sandbox/permissions, profilelaunch, MCPinitialize/list, formpostcondition иcleanupтолькособственнойfixture. Websitepermissionpromptsнельзя автоматическиgrantпооднойинструкции.

## Ограничения

ЗакрытыйC++core не изменён и не пересобран. ВmacOScandidate пока не включена публичнаяGeoLiteбаза: доbrowserlaunchпользовательдолжен обеспечить publicGeoIPчерезdocumentedDonutdataflow; это отдельнаязадачапроверки. НиmacOSGUI/CBrowser ни notarized/publicrelease вэтойсессии не заявленыготовыми.
