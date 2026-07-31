import type { AssetType } from "./types";

// The underlying AssetType value ("Stock" | "Crypto") is a wire format shared with
// the API and must stay exactly "Crypto" -- this only maps it to a friendlier word
// for display, e.g. page headers and placeholders.
export function assetTypeLabel(assetType: AssetType): string {
  return assetType === "Crypto" ? "Cryptocurrency" : assetType;
}
