import os
import logging
import aiohttp
import discord

from discord.ext import commands
from discord import app_commands


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

intents = discord.Intents.default()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
LTC_WALLET = os.getenv(
    "LTC_WALLET",
    "Lg4jwAr7wHPE93EgWDzHs8moM5HLHMRLuv"
)
WALLET_NAME = os.getenv("WALLET_NAME", "Yuqii")

LTC_API = "https://api.blockcypher.com/v1/ltc/main"
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"
FRANKFURTER_API = "https://api.frankfurter.app/latest"


if not TOKEN:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN is not set. Set your bot token as an environment variable."
    )


async def get_json(url: str):
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(
                    f"API HTTP {response.status}: {text[:300]}"
                )

            return await response.json()


async def get_ltc_prices():
    data = await get_json(
        f"{COINGECKO_API}"
        "?ids=litecoin"
        "&vs_currencies=eur,usd"
    )

    litecoin = data.get("litecoin")

    if not litecoin:
        raise Exception("Litecoin price data is unavailable.")

    return (
        litecoin.get("eur", 0),
        litecoin.get("usd", 0)
    )


def wallet_component(
    wallet_name: str,
    address: str,
    balance: float,
    received: float,
    sent: float,
    transactions: int
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
            "**Received**\n"
            f"`{received:.8f} LTC`\n\n"
            "**Sent**\n"
            f"`{sent:.8f} LTC`\n\n"
            "**Transactions**\n"
            f"`{transactions}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "### Wallet Address\n"
            f"`{address}`"
        ),
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
            "**TXID**\n"
            f"`{txid}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**Input**\n"
            f"`{total_input:.8f} LTC`\n\n"
            "**Output**\n"
            f"`{total_output:.8f} LTC`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "### LTC Value\n"
            f"**EUR:** `€{ltc_eur:,.2f}`\n"
            f"**USD:** `${ltc_usd:,.2f}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**Block**\n"
            f"`{block}`\n\n"
            "**Confirmations**\n"
            f"`{confirmations}`"
        ),
    )

    view.add_item(container)

    return view


def user_component(user: discord.User):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(
            f"# {user}"
        ),
        discord.ui.MediaGallery(
            discord.MediaGalleryItem(
                media=user.display_avatar.url
            )
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**User ID**\n"
            f"`{user.id}`\n\n"
            "**Bot**\n"
            f"`{'True' if user.bot else 'False'}`\n\n"
            "**Avatar**\n"
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
        discord.ui.TextDisplay(
            f"# {guild.name}"
        ),
        discord.ui.TextDisplay(
            "**Server ID**\n"
            f"`{guild.id}`\n\n"
            "**Owner**\n"
            f"{owner}"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            f"**Members** `{guild.member_count}`\n"
            f"**Channels** `{len(guild.channels)}`\n"
            f"**Roles** `{len(guild.roles)}`\n"
            f"**Boost Level** `{guild.premium_tier}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**Created**\n"
            f"{discord.utils.format_dt(guild.created_at, 'F')}"
        ),
    )

    view.add_item(container)

    return view


def avatar_component(user: discord.User):
    view = discord.ui.LayoutView(timeout=None)

    container = discord.ui.Container(
        discord.ui.TextDisplay(
            f"# Avatar from {user}"
        ),
        discord.ui.MediaGallery(
            discord.MediaGalleryItem(
                media=user.display_avatar.url
            )
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**User ID:** "
            f"`{user.id}`\n\n"
            f"[Open Avatar]({user.display_avatar.url})"
        ),
    )

    view.add_item(container)

    return view


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
            "**Before Tax**\n"
            f"`{robux:,} Robux`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**30% Tax**\n"
            f"`{tax:,} Robux`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "### After Tax\n"
            f"**`{after_tax:,} Robux`**"
        ),
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
            "**EUR Amount**\n"
            f"`€{eur:,.2f}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**USD Amount**\n"
            f"`${usd:,.2f}`"
        ),
        discord.ui.Separator(),
        discord.ui.TextDisplay(
            "**Exchange Rate**\n"
            f"`1 EUR = {rate:.4f} USD`"
        ),
    )

    view.add_item(container)

    return view


class YuqiiBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        synced = await self.tree.sync()

        logging.info(
            f"{len(synced)} global slash commands synchronized."
        )

    async def on_ready(self):
        logging.info(
            f"Bot online: {self.user} ({self.user.id})"
        )


bot = YuqiiBot()


@bot.tree.command(
    name="yuqiiwallet",
    description="Show my wallet information"
)
async def yuqiiwallet(
    interaction: discord.Interaction
):
    await interaction.response.defer()

    try:
        data = await get_json(
            f"{LTC_API}/addrs/{LTC_WALLET}/balance"
        )

        balance = data.get("balance", 0) / 100_000_000
        received = data.get("total_received", 0) / 100_000_000
        sent = data.get("total_sent", 0) / 100_000_000
        transactions = data.get("n_tx", 0)

        view = wallet_component(
            WALLET_NAME,
            LTC_WALLET,
            balance,
            received,
            sent,
            transactions
        )

        await interaction.followup.send(
            view=view
        )

    except Exception as error:
        await interaction.followup.send(
            "Wallet could not be loaded.\n"
            f"`{error}`"
        )


@bot.tree.command(
    name="ltcwallet",
    description="Show information about an LTC wallet"
)
@app_commands.describe(
    address="Litecoin wallet address"
)
async def ltcwallet(
    interaction: discord.Interaction,
    address: str
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

        view = wallet_component(
            "Litecoin Wallet",
            address,
            balance,
            received,
            sent,
            transactions
        )

        await interaction.followup.send(
            view=view
        )

    except Exception as error:
        await interaction.followup.send(
            "Wallet could not be loaded.\n"
            f"`{error}`"
        )


@bot.tree.command(
    name="ltctx",
    description="Show information about an LTC transaction"
)
@app_commands.describe(
    txid="Litecoin transaction hash"
)
async def ltctx(
    interaction: discord.Interaction,
    txid: str
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

        block = data.get(
            "block_height",
            "Pending"
        )

        confirmations = data.get(
            "confirmations",
            0
        )

        ltc_eur_price, ltc_usd_price = await get_ltc_prices()

        ltc_eur = total_output * ltc_eur_price
        ltc_usd = total_output * ltc_usd_price

        view = transaction_component(
            data.get("hash", txid),
            total_input,
            total_output,
            ltc_eur,
            ltc_usd,
            str(block),
            confirmations
        )

        await interaction.followup.send(
            view=view
        )

    except Exception as error:
        await interaction.followup.send(
            "Transaction could not be loaded.\n"
            f"`{error}`"
        )


@bot.tree.command(
    name="eurusd",
    description="Convert EUR to USD"
)
@app_commands.describe(
    amount="Amount in EUR"
)
async def eurusd(
    interaction: discord.Interaction,
    amount: float
):
    if amount <= 0:
        await interaction.response.send_message(
            "The amount must be greater than 0.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        data = await get_json(
            f"{FRANKFURTER_API}?from=EUR&to=USD"
        )

        rate = data["rates"]["USD"]
        usd = amount * rate

        view = eurusd_component(
            amount,
            usd,
            rate
        )

        await interaction.followup.send(
            view=view
        )

    except Exception as error:
        await interaction.followup.send(
            "Exchange rate could not be loaded.\n"
            f"`{error}`"
        )


@bot.tree.command(
    name="robloxtax",
    description="Calculate Roblox 30% tax"
)
@app_commands.describe(
    robux="Robux amount before tax"
)
async def robloxtax(
    interaction: discord.Interaction,
    robux: int
):
    if robux <= 0:
        await interaction.response.send_message(
            "The Robux amount must be greater than 0.",
            ephemeral=True
        )
        return

    tax = int(robux * 0.30)
    after_tax = robux - tax

    view = roblox_tax_component(
        robux,
        tax,
        after_tax
    )

    await interaction.response.send_message(
        view=view
    )


@bot.tree.command(
    name="user",
    description="Discord user lookup"
)
@app_commands.describe(
    user="Discord user"
)
async def user_lookup(
    interaction: discord.Interaction,
    user: discord.User
):
    await interaction.response.send_message(
        view=user_component(user),
        ephemeral=True
    )


@bot.tree.command(
    name="avatar",
    description="Show a user's avatar"
)
@app_commands.describe(
    user="Optional Discord user"
)
async def avatar(
    interaction: discord.Interaction,
    user: discord.User | None = None
):
    user = user or interaction.user

    await interaction.response.send_message(
        view=avatar_component(user)
    )


@bot.tree.command(
    name="serverinfo",
    description="Show information about the server"
)
async def serverinfo(
    interaction: discord.Interaction
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command only works on a server.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        view=server_component(
            interaction.guild
        )
    )


if __name__ == "__main__":
    bot.run(TOKEN)
