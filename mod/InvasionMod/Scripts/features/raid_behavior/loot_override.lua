-- Loot override (change update-banditry-rebellion-raid): a map from a unit to a list of goods.
-- When the body of such a unit reaches the corpse pit, the pit gets these goods and the entry ends.
-- The module is generic: it knows units and goods, not rebellions. Any feature may call `set`.
--
-- Saving: ModState has no removal and needs registered keys, so the map uses fixed string slots
-- `loot_slot_1` .. `loot_slot_<N>`. One slot holds one unit as "<squad>_<index>_<good>x<count>-<good>x<count>".
-- A cleared slot is the empty string. A slot is written at once on set, take and drop.
--
-- Unit key: the session key is the address of the SMUnit (a body is the same object as the live unit). The saved key is
-- squad id plus the index of the unit in its squad. After a load the game builds new objects, so `relink` gives the
-- entries of a squad to the units of that squad in order (the fallback of design.md; a real-game test checks it).
local M = {}

local SLOT_PREFIX = "loot_slot_"
local MAX_SLOT_CHARS = 900     -- ModState allows 1023 characters for a whole entry; the key and the prefix take about 30
M.BODY_DAYS = 30               -- a body leaves the game after about 30 game days (spike corpse-pit-loot)

---------------------------------------------------------------------------------------------
-- Slot text
---------------------------------------------------------------------------------------------

-- goods: a list of good ids (one entry for each item). Returns the slot text.
function M.encode(squad, index, goods)
    local counts, ids = {}, {}
    for _, id in ipairs(goods) do
        if counts[id] == nil then ids[#ids + 1] = id end
        counts[id] = (counts[id] or 0) + 1
    end
    table.sort(ids)
    local parts = {}
    for _, id in ipairs(ids) do parts[#parts + 1] = string.format("%dx%d", id, counts[id]) end
    return string.format("%d_%d_%s", squad, index, table.concat(parts, "-"))
end

-- Returns squad, index, goods (a list of ids), or nil and a reason.
function M.decode(text)
    local squad, index, rest = text:match("^(%d+)_(%d+)_(.+)$")
    if squad == nil then return nil, "bad slot text: " .. text end
    local goods = {}
    for id, count in rest:gmatch("(%d+)x(%d+)") do
        for _ = 1, tonumber(count) do goods[#goods + 1] = tonumber(id) end
    end
    if #goods == 0 then return nil, "no goods in slot text: " .. text end
    return tonumber(squad), tonumber(index), goods
end

---------------------------------------------------------------------------------------------
-- The map
---------------------------------------------------------------------------------------------

-- store: { slots = N, get = function(i) -> text, set = function(i, text) }. log: { info, warn, error } taking (tag, message).
function M.new(store, log)
    local self = { entries = {}, by_address = {}, log = log, tag = "InvasionMod.loot_override" }

    local function free_slot()
        for slot = 1, store.slots do
            if store.get(slot) == "" then return slot end
        end
        return nil
    end

    local function forget(entry)
        store.set(entry.slot, "")
        self.entries[entry.slot] = nil
        if entry.address ~= nil and self.by_address[entry.address] == entry then self.by_address[entry.address] = nil end
    end

    -- ref: { address, squad, index }. goods: a list of ids. Returns true, or nil and a reason (the unit then gives the config loot).
    function self.set(ref, goods)
        if #goods == 0 then return true end
        local text = M.encode(ref.squad, ref.index, goods)
        if #text > MAX_SLOT_CHARS then
            self.log.error(self.tag, "LOOT_OVERRIDE entry too long, dropped: " .. #text .. " characters")
            return nil, "entry too long"
        end
        if self.by_address[ref.address] ~= nil then forget(self.by_address[ref.address]) end
        local slot = free_slot()
        if slot == nil then
            self.log.error(self.tag, string.format("LOOT_OVERRIDE all %d slots are full, entry dropped (squad %d unit %d)", store.slots, ref.squad, ref.index))
            return nil, "slots full"
        end
        store.set(slot, text)
        local entry = { slot = slot, squad = ref.squad, index = ref.index, goods = goods, address = ref.address }
        self.entries[slot] = entry
        self.by_address[ref.address] = entry
        return true
    end

    function self.get(address)
        local entry = self.by_address[address]
        return entry and entry.goods or nil
    end

    -- Get and clear.
    function self.take(address)
        local entry = self.by_address[address]
        if entry == nil then return nil end
        forget(entry)
        return entry.goods
    end

    function self.drop(address, reason)
        local entry = self.by_address[address]
        if entry == nil then return end
        self.log.info(self.tag, string.format("LOOT_OVERRIDE dropped slot=%d squad=%d unit=%d reason=%s", entry.slot, entry.squad, entry.index, reason))
        forget(entry)
    end

    function self.clear_all()
        for _, entry in pairs(self.entries) do forget(entry) end
    end

    function self.count()
        local total = 0
        for _ in pairs(self.entries) do total = total + 1 end
        return total
    end

    -- The entries as a list ordered by slot (for the state command and the tests).
    function self.list()
        local rows = {}
        for slot = 1, store.slots do
            local entry = self.entries[slot]
            if entry ~= nil then
                rows[#rows + 1] = { slot = slot, squad = entry.squad, index = entry.index, goods = entry.goods, linked = entry.address ~= nil, dead_day = entry.dead_day }
            end
        end
        return rows
    end

    function self.addresses()
        local set = {}
        for address, entry in pairs(self.by_address) do set[address] = entry end
        return set
    end

    -- Forget the memory and read all slots again (after a load: the objects of the old game are gone).
    function self.load_saved()
        self.entries, self.by_address = {}, {}
        local loaded = 0
        for slot = 1, store.slots do
            local text = store.get(slot)
            if text ~= "" then
                local squad, index, goods = M.decode(text)
                if squad == nil then
                    self.log.error(self.tag, "LOOT_OVERRIDE slot " .. slot .. " is not readable and is cleared: " .. tostring(index))
                    store.set(slot, "")
                else
                    self.entries[slot] = { slot = slot, squad = squad, index = index, goods = goods }
                    loaded = loaded + 1
                end
            end
        end
        return loaded
    end

    -- units_by_squad: squad id -> list of { address }, in the order of the game. Entries without a unit stay unlinked.
    -- Returns the number of linked and of still unlinked entries.
    function self.relink(units_by_squad)
        local waiting = {}
        for _, entry in pairs(self.entries) do
            if entry.address == nil then
                waiting[entry.squad] = waiting[entry.squad] or {}
                table.insert(waiting[entry.squad], entry)
            end
        end
        local linked, unlinked = 0, 0
        for squad, entries in pairs(waiting) do
            table.sort(entries, function(a, b) return a.index < b.index end)
            local units = units_by_squad[squad] or {}
            for position, entry in ipairs(entries) do
                local unit = units[position]
                if unit ~= nil and self.by_address[unit.address] == nil then
                    entry.address = unit.address
                    self.by_address[unit.address] = entry
                    linked = linked + 1
                else
                    unlinked = unlinked + 1
                end
            end
        end
        return linked, unlinked
    end

    -- Drop (and log) every entry that has no unit. Returns the number dropped.
    function self.drop_unlinked()
        local dropped = 0
        for _, entry in pairs(self.entries) do
            if entry.address == nil then
                self.log.warn(self.tag, string.format("LOOT_OVERRIDE lost slot=%d squad=%d unit=%d: no unit found after the load", entry.slot, entry.squad, entry.index))
                forget(entry)
                dropped = dropped + 1
            end
        end
        return dropped
    end

    -- One look at the units. `seen` maps an address to { dead = bool } for the units the game still lists.
    -- A living unit that the game no longer lists left the map: its entry ends. A dead unit keeps its entry (its body
    -- may wait for the pit) until `BODY_DAYS` game days passed since its death. Returns the number of dropped entries.
    function self.poll(seen, today)
        local dropped = 0
        for address, entry in pairs(self.by_address) do
            local now = seen[address]
            if entry.dead_day == nil and now ~= nil and now.dead then entry.dead_day = today end
            if entry.dead_day == nil and now == nil then
                self.drop(address, "unit left the map")
                dropped = dropped + 1
            elseif entry.dead_day ~= nil and today ~= nil and today - entry.dead_day > M.BODY_DAYS then
                self.drop(address, "body expired")
                dropped = dropped + 1
            end
        end
        return dropped
    end

    -- The pit received `bodies` new bodies. Pay the entries of dead units, the oldest death first.
    -- Returns the goods to add (good id -> amount) and the number of bodies paid.
    function self.pay(bodies)
        local dead = {}
        for _, entry in pairs(self.entries) do
            if entry.dead_day ~= nil then dead[#dead + 1] = entry end
        end
        table.sort(dead, function(a, b)
            if a.dead_day ~= b.dead_day then return a.dead_day < b.dead_day end
            return a.slot < b.slot
        end)
        local goods, paid = {}, 0
        for _, entry in ipairs(dead) do
            if paid >= bodies then break end
            for _, id in ipairs(entry.goods) do goods[id] = (goods[id] or 0) + 1 end
            paid = paid + 1
            forget(entry)
        end
        return goods, paid
    end

    return self
end

---------------------------------------------------------------------------------------------
-- The ModState store
---------------------------------------------------------------------------------------------

-- Register the slots in `state` (a ModState) and return a store for M.new. The slots are registered with the state
-- marked as not loaded, so the Tags are read once and not 200 times.
function M.state_store(state, slots)
    local was_loaded = state.loaded
    state.loaded = false
    for slot = 1, slots do state:register(SLOT_PREFIX .. slot, "", "string") end
    if was_loaded then state:load() end
    return {
        slots = slots,
        get = function(slot) return state:get(SLOT_PREFIX .. slot) end,
        set = function(slot, text) state:set(SLOT_PREFIX .. slot, text) end,
    }
end

return M
