# RiggedCombat

A Paper plugin for Minecraft 1.21.11 that prevents specific players from dying when they have no Totem of Undying.

## How It Works

- Players on the rigged list **cannot die** when they have no totem in either hand — their health is capped at half a heart.
- If they **have a totem**, damage works normally and the totem pops as usual.

## Commands

| Command | Description |
|---|---|
| `/rc add <player>` | Add a player to the rigged list |
| `/rc remove <player>` | Remove a player from the rigged list |
| `/rc reload` | Reload the config without restarting |

Aliases: `/riggedcombat`, `/rigged`, `/rc`

## Permission

| Permission | Description | Default |
|---|---|---|
| `rc.editlist` | Access to all `/rc` commands | OP |

Works with **LuckPerms** — grant with `/lp user <name> permission set rc.editlist true`

## Config (`config.yml`)

Everything is customizable — messages, minimum health threshold, etc. Supports `&` color codes.

## Building from Source

To build the project yourself, ensure you have **Java 21**, **Maven**, and **Python 3** installed, then run:

```bash
chmod +x build.sh
./build.sh
```

The final protected JAR will be located at `target/riggedcombat-1.0-SNAPSHOT.jar`.

## Security & Transparency (For Moderators)

This project uses an obfuscation pipeline to protect its logic from casual reverse-engineering. However, we are committed to being fully transparent with platform moderators. 

For a detailed breakdown of the tools and methods used to protect the JAR, please see [OBFUSCATION.md](OBFUSCATION.md).

## License

This project is for private use. All rights reserved.

---
**Author:** xcloud
