import os
import logging
import asyncio 
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


TOKEN = os.getenv("DISCORD_TOKEN")

LTC_WALLET = "Lg4jwAr7wHPE93EgWDzHs8moM5HLHMRLuv"

WALLET_NAME = ("WALLET_NAME", "Yuqii")
LTC_API = "https://api.blockcypher.com/v1/ltc/main"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


intents = discord.Intents.default()


class YuqiiBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
        )
    async def setup_hook(self):
        synced = await self.tree.sync()
        logging.info("%s global slash commands synchronized.", len(synced))
    async def on_ready(self):
        logging.info("Bot online: %s (%s)", self.user, self.user.id)

bot = YuqiiBot()
async def get_json(url: str):
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            if response.status != 200:
                text = await response.text()
                raise RuntimeError(
                    f"API HTTP {response.status}: {text[:300]}"
                )

            return await response.json()


def wallet_component(
    wallet_name: str,
    address: str,
    balance: float,
    received: float,
    sent: float,
    transactions: int,
):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(
            f"# {wallet_name} Wallet"
        ),
        discord.ui.TextDisplay(
            "### Litecoin Balance\n"
            f"**{balance:.8f} LTC**"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**Empfangen**\n"
            f"`{received:.8f} LTC`\n\n"
            f"**Gesendet**\n"
            f"`{sent:.8f} LTC`\n\n"
            f"**Transaktionen**\n"
            f"`{transactions}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "### Wallet-Adresse\n"
            f"`{address}`"
        ),
    )

    view.add_item(container)
    return view


def transaction_component(
    txid: str,
    total_input: float,
    total_output: float,
    block: str,
    confirmations: int,
):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay("# Litecoin Transaction"),
        discord.ui.TextDisplay(
            f"**TXID**\n"
            f"`{txid}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**Input**\n"
            f"`{total_input:.8f} LTC`\n\n"
            f"**Output**\n"
            f"`{total_output:.8f} LTC`\n\n"
            f"**Block**\n"
            f"`{block}`\n\n"
            f"**Confirmations**\n"
            f"`{confirmations}`"
        ),
    )

    view.add_item(container)
    return view


def user_component(user: discord.User):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(f"# {user}"),
        discord.ui.MediaGallery(
            discord.MediaGalleryItem(
                media=user.display_avatar.url
            )
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**User ID**\n"
            f"`{user.id}`\n\n"
            f"**Bot**\n"
            f"`{'True' if user.bot else 'False'}`\n\n"
            f"**Avatar**\n"
            f"[Open Avatar]({user.display_avatar.url})"
        ),
    )

    view.add_item(container)
    return view


def server_component(guild: discord.Guild):
    owner = (
        guild.owner.mention
        if guild.owner
        else f"`{guild.owner_id}`"
    )

    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(f"# {guild.name}"),
        discord.ui.TextDisplay(
            f"**Server ID**\n"
            f"`{guild.id}`\n\n"
            f"**Owner**\n"
            f"{owner}"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**Member**  `{guild.member_count}`\n"
            f"**Channels**  `{len(guild.channels)}`\n"
            f"**Rollen**  `{len(guild.roles)}`\n"
            f"**Boost Level**  `{guild.premium_tier}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**Erstellt**\n"
            f"{discord.utils.format_dt(guild.created_at, 'F')}"
        ),
    )

    view.add_item(container)
    return view


def avatar_component(user: discord.User):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(f"# Avatar from {user}"),
        discord.ui.MediaGallery(
            discord.MediaGalleryItem(
                media=user.display_avatar.url
            )
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**User ID:** `{user.id}`\n\n"
            f"[Open Avatar]({user.display_avatar.url})"
        ),
    )

    view.add_item(container)
    return view


async def send_error(interaction: discord.Interaction, error: Exception):
    message = f"An error occurred:\n`{error}`"

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)

yuqii = app_commands.Group(
    name="yuqii",
    description="Yuqii utilities and tools",
    allowed_contexts=app_commands.AppCommandContext(
        guild=True,
        dm_channel=True,
        private_channel=True,
    ),
    allowed_installs=app_commands.AppInstallationType(
        guild=True,
        user=True,
    ),
)


@yuqii.command(
    name="wallet",
    description="Show the configured Yuqii Litecoin wallet",
)
async def yuqii_wallet(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        data = await get_json(
            f"{LTC_API}/addrs/{LTC_WALLET}/balance"
        )

        balance = data.get("balance", 0) / 100_000_000
        received = data.get("total_received", 0) / 100_000_000
        sent = data.get("total_sent", 0) / 100_000_000
        transactions = data.get("n_tx", 0)

        await interaction.followup.send(
            view=wallet_component(
                WALLET_NAME,
                LTC_WALLET,
                balance,
                received,
                sent,
                transactions,
            )
        )

    except Exception as error:
        await send_error(interaction, error)


@yuqii.command(
    name="ltcwallet",
    description="Show information about an LTC wallet",
)
@app_commands.describe(
    address="Litecoin wallet address",
)
async def yuqii_ltcwallet(
    interaction: discord.Interaction,
    address: str,
):
    await interaction.response.defer()
    try:
        data = await get_json(
            f"{LTC_API}/addrs/{address}/balance"
        )
        balance = data.get("balance", 0) / 100_000_000
        received = data.get("total_received", 0) / 100_000_000
        sent = data.get("total_sent", 0) / 100_000_000
        transactions = data.get("n_tx", 0)

        await interaction.followup.send(
            view=wallet_component(
                "Litecoin Wallet",
                address,
                balance,
                received,
                sent,
                transactions,
            )
        )

    except Exception as error:
        await send_error(interaction, error)

bot.allowed_contexts = app_commands.AppCommandContext(
    guild=True,
    dm_channel=True,
    private_channel=True,
)
bot.allowed_installs = app_commands.AppInstallationType(
    guild=True,
    user=True,
)
@yuqii.command(
    name="ltctx",
    description="Show information about an LTC transaction",
)
@app_commands.describe(
    txid="Litecoin transaction hash",
)
async def yuqii_ltctx(
    interaction: discord.Interaction,
    txid: str,
):
    await interaction.response.defer()

    try:
        data = await get_json(
            f"{LTC_API}/txs/{txid}"
        )

        total_input = sum(
            item.get("output_value", 0)
            for item in data.get("inputs", [])
        ) / 100_000_000

        total_output = sum(
            item.get("value", 0)
            for item in data.get("outputs", [])
        ) / 100_000_000

        block = data.get("block_height", "Pending")
        confirmations = data.get("confirmations", 0)

        await interaction.followup.send(
            view=transaction_component(
                data.get("hash", txid),
                total_input,
                total_output,
                str(block),
                confirmations,
            )
        )

    except Exception as error:
        await send_error(interaction, error)

@yuqii.command(
    name="user",
    description="Discord User Lookup",
)
@app_commands.describe(
    user="Discord user",
)
async def yuqii_user(
    interaction: discord.Interaction,
    user: discord.User,
):
    await interaction.response.send_message(
        view=user_component(user),
        ephemeral=True,
    )

@yuqii.command(
    name="avatar",
    description="Show a user's avatar",
)
@app_commands.describe(
    user="Optional Discord user",
)
async def yuqii_avatar(
    interaction: discord.Interaction,
    user: discord.User | None = None,
):
    user = user or interaction.user

    await interaction.response.send_message(
        view=avatar_component(user),
    )

@yuqii.command(
    name="serverinfo",
    description="Show information about the current server",
)
async def yuqii_serverinfo(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Command can only be used in a server.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        view=server_component(interaction.guild)
    )




def roblox_tax_component(
    robux: int,
    tax: int,
    after_tax: int
):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(
            "# Roblox Tax Calculator"
        ),
        discord.ui.TextDisplay(
            f"**Before Tax**\n"
            f"`{robux:,} Robux`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**30% Tax**\n"
            f"`{tax:,} Robux`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"### After Tax\n"
            f"**`{after_tax:,} Robux`**"
        ),
        accent_colour=discord.Colour.red()
    )

    view.add_item(container)
    return view

def eurusd_component(
    eur: float,
    usd: float,
    rate: float
):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(
            "# EUR → USD Converter"
        ),
        discord.ui.TextDisplay(
            f"**EUR Amount**\n"
            f"`€{eur:,.2f}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**USD Amount**\n"
            f"`${usd:,.2f}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**Exchange Rate**\n"
            f"`1 EUR = {rate:.4f} USD`"
        ),
        accent_colour=discord.Colour.green()
    )

    view.add_item(container)
    return view


def transaction_component(
    txid: str,
    total_input: float,
    total_output: float,
    ltc_eur: float,
    ltc_usd: float,
    block: str,
    confirmations: int
):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(
            "# Litecoin Transaction"
        ),
        discord.ui.TextDisplay(
            f"**TXID**\n"
            f"`{txid}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**Input**\n"
            f"`{total_input:.8f} LTC`\n\n"
            f"**Output**\n"
            f"`{total_output:.8f} LTC`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**LTC Value**\n"
            f"`€{ltc_eur:,.2f}`\n"
            f"`${ltc_usd:,.2f}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**Block**\n"
            f"`{block}`\n\n"
            f"**Confirmations**\n"
            f"`{confirmations}`"
        ),
        accent_colour=discord.Colour.gold()
    )

    view.add_item(container)
    return view


bot.tree.add_command(yuqii)

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN is not set. "
            "Set your bot token as an environment variable."
        )

if __name__ == "__main__":
    bot.run(TOKEN)
