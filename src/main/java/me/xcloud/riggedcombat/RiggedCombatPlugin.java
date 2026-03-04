package me.xcloud.riggedcombat;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Material;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

public class RiggedCombatPlugin extends JavaPlugin implements Listener, CommandExecutor, TabCompleter {

    private final Set<UUID> riggedPlayers = new HashSet<>();

    // Configurable values
    private double minHealth;
    private String msgNoPermission;
    private String msgUsage;
    private String msgPlayerNotFound;
    private String msgPlayerAdded;
    private String msgPlayerAlreadyInList;
    private String msgPlayerRemoved;
    private String msgPlayerNotInList;
    private String msgReloaded;
    private String msgPluginEnabled;
    private String msgPluginDisabled;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        loadConfigValues();
        loadRiggedPlayers();

        getServer().getPluginManager().registerEvents(this, this);
        getCommand("riggedcombat").setExecutor(this);
        getCommand("riggedcombat").setTabCompleter(this);

        getLogger().info(msgPluginEnabled);
    }

    @Override
    public void onDisable() {
        saveRiggedPlayers();
        getLogger().info(msgPluginDisabled);
    }

    private void loadConfigValues() {
        minHealth = getConfig().getDouble("settings.min-health", 1.0);

        msgNoPermission = color(getConfig().getString("messages.no-permission", "&cYou do not have permission to use this command."));
        msgUsage = color(getConfig().getString("messages.usage", "&cUsage: /{label} [add|remove|reload] <player>"));
        msgPlayerNotFound = color(getConfig().getString("messages.player-not-found", "&cPlayer not found or not online."));
        msgPlayerAdded = color(getConfig().getString("messages.player-added", "&a{player} has been added to the rigged combat list."));
        msgPlayerAlreadyInList = color(getConfig().getString("messages.player-already-in-list", "&e{player} is already in the list."));
        msgPlayerRemoved = color(getConfig().getString("messages.player-removed", "&a{player} has been removed from the rigged combat list."));
        msgPlayerNotInList = color(getConfig().getString("messages.player-not-in-list", "&e{player} is not in the list."));
        msgReloaded = color(getConfig().getString("messages.reloaded", "&aRiggedCombat config reloaded successfully."));
        msgPluginEnabled = getConfig().getString("messages.plugin-enabled", "RiggedCombat Plugin enabled.");
        msgPluginDisabled = getConfig().getString("messages.plugin-disabled", "RiggedCombat Plugin disabled.");
    }

    private void loadRiggedPlayers() {
        riggedPlayers.clear();
        List<String> savedPlayers = getConfig().getStringList("rigged-players");
        for (String uuidStr : savedPlayers) {
            try {
                riggedPlayers.add(UUID.fromString(uuidStr));
            } catch (IllegalArgumentException ignored) {}
        }
    }

    private void saveRiggedPlayers() {
        List<String> toSave = new ArrayList<>();
        for (UUID uuid : riggedPlayers) {
            toSave.add(uuid.toString());
        }
        getConfig().set("rigged-players", toSave);
        saveConfig();
    }

    private String color(String msg) {
        return ChatColor.translateAlternateColorCodes('&', msg);
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!sender.hasPermission("rc.editlist")) {
            sender.sendMessage(msgNoPermission);
            return true;
        }

        if (args.length < 1) {
            sender.sendMessage(msgUsage.replace("{label}", label));
            return true;
        }

        String action = args[0].toLowerCase();

        // Handle reload
        if (action.equals("reload")) {
            reloadConfig();
            loadConfigValues();
            loadRiggedPlayers();
            sender.sendMessage(msgReloaded);
            return true;
        }

        // All other actions require a player arg
        if (args.length < 2) {
            sender.sendMessage(msgUsage.replace("{label}", label));
            return true;
        }

        String targetName = args[1];
        Player target = Bukkit.getPlayer(targetName);

        if (target == null) {
            sender.sendMessage(msgPlayerNotFound);
            return true;
        }

        UUID targetUUID = target.getUniqueId();

        if (action.equals("add")) {
            if (riggedPlayers.add(targetUUID)) {
                sender.sendMessage(msgPlayerAdded.replace("{player}", target.getName()));
                saveRiggedPlayers();
            } else {
                sender.sendMessage(msgPlayerAlreadyInList.replace("{player}", target.getName()));
            }
        } else if (action.equals("remove")) {
            if (riggedPlayers.remove(targetUUID)) {
                sender.sendMessage(msgPlayerRemoved.replace("{player}", target.getName()));
                saveRiggedPlayers();
            } else {
                sender.sendMessage(msgPlayerNotInList.replace("{player}", target.getName()));
            }
        } else {
            sender.sendMessage(msgUsage.replace("{label}", label));
        }

        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        List<String> completions = new ArrayList<>();
        if (args.length == 1) {
            completions.add("add");
            completions.add("remove");
            completions.add("reload");
            return filterCompletions(completions, args[0]);
        } else if (args.length == 2 && !args[0].equalsIgnoreCase("reload")) {
            for (Player p : Bukkit.getOnlinePlayers()) {
                completions.add(p.getName());
            }
            return filterCompletions(completions, args[1]);
        }
        return completions;
    }

    private List<String> filterCompletions(List<String> list, String prefix) {
        List<String> result = new ArrayList<>();
        for (String s : list) {
            if (s.toLowerCase().startsWith(prefix.toLowerCase())) {
                result.add(s);
            }
        }
        return result;
    }

    @EventHandler(priority = EventPriority.HIGHEST, ignoreCancelled = true)
    public void onPlayerDamage(EntityDamageEvent event) {
        if (!(event.getEntity() instanceof Player player)) {
            return;
        }

        if (!riggedPlayers.contains(player.getUniqueId())) {
            return;
        }

        double health = player.getHealth();
        double damage = event.getFinalDamage();

        PlayerInventory inv = player.getInventory();
        ItemStack mainHand = inv.getItemInMainHand();
        ItemStack offHand = inv.getItemInOffHand();

        boolean hasTotem = (mainHand != null && mainHand.getType() == Material.TOTEM_OF_UNDYING) ||
                           (offHand != null && offHand.getType() == Material.TOTEM_OF_UNDYING);

        // If player has a totem, let damage through normally (totem will pop)
        if (hasTotem) {
            return;
        }

        // If already at or below min health, cancel all damage
        if (health <= minHealth) {
            event.setCancelled(true);
            return;
        }

        // If this hit would bring them to or below min health, cancel and set to min
        if (health - damage <= minHealth) {
            event.setCancelled(true);
            player.setHealth(minHealth);
        }
    }
}
