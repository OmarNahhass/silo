import type { AssetType } from "./types";

export function assetTypeLabel(assetType: AssetType): string {
  return assetType === "Crypto" ? "Cryptocurrency" : assetType;
}
