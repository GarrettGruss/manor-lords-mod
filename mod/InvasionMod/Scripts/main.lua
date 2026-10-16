-- InvasionMod: one Lua mod made of separate features (spec 22).
-- It loads ManorCore, config.lua, then each enabled feature in dependency order.
-- Paths: UE4SS puts this Scripts folder on package.path, so "feature_loader" and "features.<name>.init" resolve here.
local core = require("ManorCore")
local TAG = "InvasionMod"

local loader = require("feature_loader")
local config = require("config")
local feature_list = require("feature_list")

local ok, result = pcall(loader.load, feature_list, config, require, function(message) core.log.info(TAG, message) end)
if not ok then
    core.log.error(TAG, "load failed: " .. tostring(result))
    error(result, 0)
end
core.log.info(TAG, "ready, features: " .. table.concat(result, ", "))
