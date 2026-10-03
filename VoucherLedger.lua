if _G.VoucherLedger then return end

local HUD_OFFSET_X = -2.75
local HUD_OFFSET_Y = 0

local ledger = {
    hud_dirty = true,
}
_G.VoucherLedger = ledger

local function voucher_key(card)
    return card and card.config and card.config.center_key
end

local function rebuild_voucher_history(cards)
    local history, card_keys = {}, {}
    for index, card in ipairs(cards) do
        local key = voucher_key(card)
        local center = key and G.P_CENTERS[key]
        card_keys[index] = key
        if key and center and center.set == 'Voucher' then
            history[#history + 1] = key
        end
    end

    ledger.voucher_cards = cards
    ledger.voucher_card_keys = card_keys
    ledger.history = history
    ledger.history_signature = table.concat(history, '\31')
    G.GAME.voucher_ledger = history
    return history
end

local function voucher_history()
    if not G or not G.GAME then return {} end

    local cards = G.vouchers and G.vouchers.cards
    if type(cards) ~= 'table' then
        return type(G.GAME.voucher_ledger) == 'table' and G.GAME.voucher_ledger or {}
    end

    local card_keys = ledger.voucher_card_keys
    if ledger.voucher_cards ~= cards or not card_keys or #card_keys ~= #cards then
        return rebuild_voucher_history(cards)
    end
    for index, card in ipairs(cards) do
        if card_keys[index] ~= voucher_key(card) then
            return rebuild_voucher_history(cards)
        end
    end
    return ledger.history
end

function ledger.record(card)
    local center = card and card.config and card.config.center
    if center and center.set == 'Voucher' then ledger.hud_dirty = true end
end

local function can_show_hud()
    return G and G.HUD and G.GAME and G.STATES and (
           G.STATE == G.STATES.SHOP
        or G.STATE == G.STATES.SELECTING_HAND
        or G.STATE == G.STATES.HAND_PLAYED
        or G.STATE == G.STATES.BLIND_SELECT
        or G.STATE == G.STATES.BUFFOON_PACK
        or G.STATE == G.STATES.STANDARD_PACK
        or G.STATE == G.STATES.SMODS_BOOSTER_OPENED
        or G.STATE == G.STATES.SMODS_REDEEM_VOUCHER
    )
end

local function remove_voucher_row()
    if ledger.voucher_row then ledger.voucher_row:remove() end
    ledger.voucher_row = nil
end

local function voucher_row(history)
    local sources = G.vouchers and G.vouchers.cards or {}
    local row = CardArea(
        0,
        0,
        G.CARD_H,
        math.max(G.TILE_H or G.CARD_W, G.CARD_W),
        {
            card_limit = #history,
            type = 'voucher',
            highlight_limit = 0,
        }
    )
    local silent = true

    for _, source in ipairs(sources) do
        local key = voucher_key(source)
        local center = key and G.P_CENTERS[key]
        if center and center.set == 'Voucher' then
            local card = copy_card(source)
            if card.ability and source.ability and source.ability.extra then
                card.ability.extra = copy_table(source.ability.extra)
            end
            if card.facing == 'back' then card:flip() end
            card:start_materialize(nil, silent)
            row:emplace(card)
            card.disable_align = true
            card.states.drag.can = false
            card.states.drag.is = false
            card.align_h_popup = function(self)
                local popup_type = 'cr'
                return {
                    major = self.children.focused_ui or self,
                    parent = self,
                    xy_bond = 'Strong',
                    r_bond = 'Weak',
                    wh_bond = 'Weak',
                    offset = {x = G.CARD_H * 0.55, y = 0},
                    type = popup_type,
                }
            end
        end
    end
    return row
end

local HOVERED_VOUCHER_X_OFFSET = 0.75

local function arrange_voucher_row()
    local row = ledger.voucher_row
    if not row then return end

    local count = #row.cards
    local center_x = row.T.x + row.T.w / 2
    local vertical_span = math.max(row.T.h - G.CARD_W, 0)
    for index, card in ipairs(row.cards) do
        local center_y = row.T.y + (count == 1 and row.T.h / 2
            or G.CARD_W / 2 + (index - 1) * vertical_span / (count - 1))
        card.voucher_ledger_x = center_x - G.CARD_W / 2
        card.voucher_ledger_y = center_y - G.CARD_H / 2
        card.T.r = math.pi / 2
        card:hard_set_T(card.voucher_ledger_x, card.voucher_ledger_y,
            G.CARD_W, G.CARD_H)
    end
end

local function lock_voucher_row()
    local row = ledger.voucher_row
    if not row then return end

    for _, card in ipairs(row.cards) do
        card.states.drag.can = false
        card.states.drag.is = false
        local target_x = card.voucher_ledger_x
        local target_y = card.voucher_ledger_y
        if card.states.hover.is then
            target_x = target_x + HOVERED_VOUCHER_X_OFFSET

        end
        if card.T.x ~= target_x or card.T.y ~= card.voucher_ledger_y
        or card.T.r ~= math.pi / 2 then
            card.T.r = math.pi / 2
            if card.states.hover.is then
                card.T.r = math.pi / 2.1
                target_y = target_y - 0.25
            end
            card:hard_set_T(target_x, target_y,
                G.CARD_W, G.CARD_H)
        end
    end
end

local function hud_definition(history)
    remove_voucher_row()
    ledger.voucher_row = voucher_row(history)
    ledger.voucher_row.T.r = 0
    ledger.voucher_row.VT.r = 0
    return {
        n = G.UIT.ROOT,
        config = {align = 'cm', padding = 0.01, colour = G.C.CLEAR},
        nodes = {{
            n = G.UIT.O,
            config = {object = ledger.voucher_row},
        }},
    }
end

function ledger.update_hud()
    local history = voucher_history()
    local hud = ledger.hud
    if not can_show_hud() or #history == 0 then
        if hud then hud:remove() end
        remove_voucher_row()
        ledger.hud, ledger.hud_anchor, ledger.hud_signature = nil, nil, nil
        return
    end

    local anchor = G.HUD
    local signature = ledger.history_signature or table.concat(history, '\31')
    if not ledger.hud_dirty and hud and ledger.hud_anchor == anchor
        and ledger.hud_signature == signature then
        lock_voucher_row()
        return
    end
    if hud then hud:remove() end
    ledger.hud = UIBox{
        definition = hud_definition(history),
        config = {
            major = anchor,
            align = 'cli',
            offset = {
                x = HUD_OFFSET_X,
                y = HUD_OFFSET_Y,
            },
            bond = 'Weak',
        },
    }
    arrange_voucher_row()
    ledger.hud_anchor = anchor
    ledger.hud_signature = signature
    ledger.hud_dirty = false
    lock_voucher_row()
end

local game_update = Game.update
function Game:update(dt)
    local result = game_update(self, dt)
    ledger.update_hud()
    return result
end
