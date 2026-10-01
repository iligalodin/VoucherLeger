# Voucher Ledger

Voucher Ledger keeps a visual record of every voucher redeemed during the current run.

## Use

Voucher Ledger mirrors Balatro's existing **Bought Vouchers** presentation: it makes front-facing copies of the redeemed voucher cards, merges every copy into one native `CardArea`, and places those copies as one locked vertical column. Each card is rotated 90° clockwise; no automatic voucher-layout groups or dragging remain. The column is capped at the game screen height, so additional vouchers compress into the same strip. A hovered voucher alone moves 0.75 units toward the screen centre, then returns to the column when hover ends. Hover information always opens at the rotated card's upper edge: the screen-right side of the voucher. The copies retain the card's normal artwork, atlas, materialize effect, glint, hover focus, and voucher description. The strip is visible in the shop, while choosing a hand, and during score calculation.

The source cards in `G.vouchers.cards` are never modified. Their keys determine which cards are copied, so custom voucher chains retain their own artwork and avoid unrelated `used_vouchers` flags.

## Install

Requires Steamodded and Lovely. Place this folder in Balatro's `Mods` directory and restart Balatro.

## Thunderstore release

Run `scripts/build-thunderstore.sh` to produce `dist/VoucherLedger-<CalVer>.zip`, then run `scripts/verify-thunderstore.sh` before uploading. The archive has Thunderstore's required root-level metadata and only the files installed for this mod.
