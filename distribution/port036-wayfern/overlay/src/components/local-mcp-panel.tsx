"use client";

import { invoke } from "@tauri-apps/api/core";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SettingsPanel } from "@/components/ui/settings-panel";
import { translateBackendError } from "@/lib/backend-errors";
import { showErrorToast, showSuccessToast } from "@/lib/toast-utils";

export function LocalMcpPanel({
  agents,
}: {
  agents: { id: string; display_name: string }[];
}) {
  const { t } = useTranslation();
  const [port, setPort] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [agent, setAgent] = useState("");
  useEffect(() => {
    let current = true;
    void invoke<{ port: number } | null>("get_mcp_config")
      .then((config) => {
        if (current) setPort(config?.port ?? null);
      })
      .catch((error) => {
        if (current) showErrorToast(translateBackendError(t, error));
      });
    return () => {
      current = false;
    };
  }, [t]);
  async function act(work: () => Promise<void>) {
    setBusy(true);
    try {
      await work();
    } catch (error) {
      showErrorToast(translateBackendError(t, error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <SettingsPanel className="mb-4 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1">
          <h3 className="font-medium">{t("integrations.local.title")}</h3>
          <p className="text-sm text-muted-foreground">
            {t("integrations.local.hint")}
          </p>
          {port !== null && (
            <code className="text-sm">http://127.0.0.1:{port}/mcp</code>
          )}
        </div>
        <Button
          disabled={busy}
          variant="outline"
          onClick={() =>
            void act(async () => {
              if (port === null)
                setPort(await invoke<number>("start_mcp_server"));
              else {
                await invoke("stop_mcp_server");
                setPort(null);
              }
            })
          }
        >
          {t(
            port === null
              ? "integrations.local.start"
              : "integrations.local.stop",
          )}
        </Button>
      </div>
      <div className="flex items-center gap-3">
        <Label htmlFor="local-mcp-agent">{t("integrations.local.agent")}</Label>
        <Select value={agent} onValueChange={setAgent} disabled={busy}>
          <SelectTrigger id="local-mcp-agent" className="flex-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {agents.map((a) => (
              <SelectItem key={a.id} value={a.id}>
                {a.display_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          disabled={busy || !agent}
          onClick={() =>
            void act(async () => {
              await invoke("add_local_mcp_to_agent", { agentId: agent });
              const config = await invoke<{ port: number } | null>(
                "get_mcp_config",
              );
              setPort(config?.port ?? null);
              showSuccessToast(t("integrations.local.installed"));
            })
          }
        >
          {t("integrations.local.install")}
        </Button>
      </div>
    </SettingsPanel>
  );
}
