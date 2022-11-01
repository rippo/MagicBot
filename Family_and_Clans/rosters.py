import disnake
import coc

from disnake.ext import commands
from CustomClasses.CustomBot import CustomClient
from CustomClasses.Roster import Roster
from main import check_commands
from Exceptions import *

class Roster_Commands(commands.Cog, name="Rosters"):

    def __init__(self, bot: CustomClient):
        self.bot = bot

    async def clan_converter(self, clan_tag: str):
        clan = await self.bot.getClan(clan_tag=clan_tag, raise_exceptions=True)
        if clan.member_count == 0:
            raise coc.errors.NotFound
        return clan

    async def player_convertor(self, player_tag: str):
        player = await self.bot.getPlayer(player_tag=player_tag, raise_exceptions=True)
        return player

    @commands.slash_command(name="roster")
    async def roster(self, ctx: disnake.ApplicationCommandInteraction):
        pass


    @roster.sub_command(name="create", description="Create a roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_create(self, ctx: disnake.ApplicationCommandInteraction, clan: coc.Clan = commands.Param(converter=clan_converter), roster_alias: str = commands.Param(name="roster_alias"), add_members_to_roster: str = commands.Param(default="No", choices=["Yes", "No"])):
        roster = Roster(bot=self.bot)
        await roster.create_roster(guild=ctx.guild, clan=clan, alias=roster_alias, add_members=(add_members_to_roster == "Yes"))
        embed = disnake.Embed(description=f"**{roster.roster_result.get('alias')}** Roster created & tied to {roster.roster_result.get('clan_name')}", color=disnake.Color.green())
        embed.set_thumbnail(url=clan.badge.url)
        await ctx.send(embed=embed)


    @roster.sub_command(name="delete", description="Delete a roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_delete(self, ctx: disnake.ApplicationCommandInteraction, roster: str):
        _roster = Roster(self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        await _roster.delete()
        embed = disnake.Embed(
            description=f"Roster - **{_roster.roster_result.get('alias')}** that was tied to {_roster.roster_result.get('clan_name')} has been **deleted**.",
            color=disnake.Color.red())
        await ctx.send(embed=embed)

    @roster.sub_command(name="clear", description="Clear a roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_clear(self, ctx: disnake.ApplicationCommandInteraction, roster: str):
        _roster = Roster(self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        await _roster.clear_roster()
        embed = disnake.Embed(
            description=f"Roster - **{_roster.roster_result.get('alias')}** that was tied to {_roster.roster_result.get('clan_name')} has been **cleared**.",
            color=disnake.Color.red())
        await ctx.send(embed=embed)

    @roster.sub_command(name="signup", description="Create a signup for a roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_create_signups(self, ctx: disnake.ApplicationCommandInteraction, roster: str):
        _roster = Roster(self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        embed = await _roster.embed()
        signup_buttons = [
            disnake.ui.Button(label="Sign Up", emoji=self.bot.emoji.yes.partial_emoji, style=disnake.ButtonStyle.green, custom_id=f"Signup_{roster}"),
            disnake.ui.Button(label="Remove Me", emoji=self.bot.emoji.no.partial_emoji, style=disnake.ButtonStyle.red,custom_id=f"RemoveMe_{roster}")
        ]
        buttons = disnake.ui.ActionRow()
        for button in signup_buttons:
            buttons.append_item(button)
        await ctx.send(embed=embed, components=[buttons])


    @roster.sub_command(name="add-player", description="Add a player to a roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_add(self, ctx: disnake.ApplicationCommandInteraction, roster: str, player: coc.Player = commands.Param(converter=player_convertor)):
        _roster = Roster(bot=self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        await _roster.add_member(player=player)
        embed = disnake.Embed(description=f"{player.name} added to **{_roster.roster_result.get('alias')}** roster.",color=disnake.Color.green())
        embed.set_thumbnail(url=_roster.roster_result.get("clan_badge"))
        await ctx.send(embed=embed, ephemeral=True)


    @roster.sub_command(name="remove-player", description="Remove a player from a roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_remove(self, ctx: disnake.ApplicationCommandInteraction, roster: str):
        await ctx.response.defer()
        _roster = Roster(bot=self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        embed = await _roster.embed(move_text="Mode: remove")
        components = await _roster.mode_components(mode="remove", player_page=0)
        await ctx.edit_original_message(embed=embed, components=components)
        msg = await ctx.original_message()

        def check(res: disnake.MessageInteraction):
            return res.message.id == msg.id

        _new_roster = Roster(bot=self.bot)
        await _new_roster.find_roster(guild=ctx.guild, alias=roster)
        new_roster = roster
        mode = "remove"
        while True:
            try:
                res: disnake.MessageInteraction = await self.bot.wait_for("message_interaction", check=check,
                                                                          timeout=600)
            except:
                await msg.edit(components=[])
                break

            if res.author.id != ctx.author.id:
                await res.send(content="Must run the command to interact with components.", ephemeral=True)
                continue
            await res.response.defer()
            try:
                if "button" in str(res.data.component_type):
                    button_value = res.data.custom_id
                    button_value = button_value.split("_")[1]
                    mode = button_value
                    if button_value == "move":
                        embed = await _roster.embed(move_text=f"Mode: {button_value} | Moving to {new_roster}")
                    else:
                        embed = await _roster.embed(move_text=f"Mode: {button_value}")
                    components = await _roster.mode_components(mode=button_value, player_page=0)
                    await res.edit_original_message(embed=embed, components=components)
                else:
                    if "players_1" in res.values or "players_2" in res.values or "players_0" in res.values:
                        for value in res.values:
                            if "players" in value:
                                page = value.split("_")[1]
                                components = await _roster.mode_components(mode=mode, player_page=int(page))
                                await res.edit_original_message(embed=embed, components=components)
                                break
                    elif any("edit_" in value for value in res.values):
                        players = await self.bot.get_players(tags=[value.split("_")[1] for value in res.values])
                        for player in players:
                            if isinstance(player, coc.errors.NotFound):
                                continue
                            if mode == "move":
                                await _roster.move_member(player=player, new_roster=_new_roster)
                            else:
                                await _roster.remove_member(player=player)
                        embed = disnake.Embed(
                            description=f"{', '.join([player.name for player in players if not isinstance(player, coc.errors.NotFound)])} moved from **{_roster.roster_result.get('alias')}** to **{_new_roster.roster_result.get('alias')}** roster",
                            color=disnake.Color.green())
                        embed.set_thumbnail(url=_new_roster.roster_result.get("clan_badge"))
                        # await res.followup.send(embed=embed, ephemeral=True)
                        await _new_roster.find_roster(guild=ctx.guild, alias=_new_roster.roster_result.get("alias"))
                        await _roster.find_roster(guild=ctx.guild, alias=_roster.roster_result.get("alias"))
                        if mode == "move":
                            embed = await _roster.embed(move_text=f"Mode: {mode} | Moving to {new_roster}")
                        else:
                            embed = await _roster.embed(move_text=f"Mode: {mode}")
                        components = await _roster.mode_components(mode=mode, player_page=0)
                        await res.edit_original_message(embed=embed, components=components)
                    elif "roster_" in res.values[0]:
                        alias = res.values[0].split("_")[1]
                        await _roster.find_roster(guild=ctx.guild, alias=alias)
                        if mode == "move":
                            embed = await _roster.embed(move_text=f"Mode: {mode} | Moving to {new_roster}")
                        else:
                            embed = await _roster.embed(move_text=f"Mode: {mode}")
                        components = await _roster.mode_components(mode=mode, player_page=0)
                        await res.edit_original_message(embed=embed, components=components)
                    elif "rostermove_" in res.values[0]:
                        alias = res.values[0].split("_")[1]
                        new_roster = alias
                        await _new_roster.find_roster(guild=ctx.guild, alias=new_roster)
                        embed = await _roster.embed(move_text=f"Mode: {mode} | Moving to {new_roster}")
                        await res.edit_original_message(embed=embed)
            except Exception as error:
                if isinstance(error, RosterAliasAlreadyExists):
                    embed = disnake.Embed(description=f"Roster with this alias already exists.",
                                          color=disnake.Color.red())
                    await res.send(embed=embed, ephemeral=True)

                if isinstance(error, RosterDoesNotExist):
                    embed = disnake.Embed(description=f"Roster with this alias does not exist. Use `/roster create`",
                                          color=disnake.Color.red())
                    await res.send(embed=embed, ephemeral=True)

                if isinstance(error, PlayerAlreadyInRoster):
                    embed = disnake.Embed(description=f"Player has already been added to this roster.",
                                          color=disnake.Color.red())
                    await res.send(embed=embed, ephemeral=True)

                if isinstance(error, PlayerNotInRoster):
                    embed = disnake.Embed(description=f"Player not found in this roster.",
                                          color=disnake.Color.red())
                    await res.send(embed=embed, ephemeral=True)


    @roster.sub_command(name="move-player", description="Move a player from one roster to another")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_move(self, ctx: disnake.ApplicationCommandInteraction, roster: str, new_roster: str = commands.Param(name="new_roster")):

        await ctx.response.defer()
        _roster = Roster(bot=self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        embed = await _roster.embed(move_text=f"Mode: Move | Moving to {new_roster}")
        components = await _roster.mode_components(mode="move", player_page=0)
        await ctx.edit_original_message(embed=embed, components=components)
        msg = await ctx.original_message()

        def check(res: disnake.MessageInteraction):
            return res.message.id == msg.id

        _new_roster = Roster(bot=self.bot)
        await _new_roster.find_roster(guild=ctx.guild, alias=new_roster)
        mode = "move"
        while True:
            try:
                res: disnake.MessageInteraction = await self.bot.wait_for("message_interaction", check=check, timeout=600)
            except:
                await msg.edit(components=[])
                break

            if res.author.id != ctx.author.id:
                await res.send(content="Must run the command to interact with components.", ephemeral=True)
                continue
            await res.response.defer()
            try:
                if "button" in str(res.data.component_type):
                    button_value = res.data.custom_id
                    button_value = button_value.split("_")[1]
                    mode = button_value
                    if button_value == "move":
                        embed = await _roster.embed(move_text=f"Mode: {button_value} | Moving to {new_roster}")
                    else:
                        embed = await _roster.embed(move_text=f"Mode: {button_value}")
                    components = await _roster.mode_components(mode=button_value, player_page=0)
                    await res.edit_original_message(embed=embed, components=components)
                else:
                    if "players_1" in res.values or "players_2" in res.values or "players_0" in res.values:
                        for value in res.values:
                            if "players" in value:
                                page = value.split("_")[1]
                                components = await _roster.mode_components(mode=mode, player_page=int(page))
                                await res.edit_original_message(embed=embed, components=components)
                                break
                    elif any("edit_" in value for value in res.values):
                        players = await self.bot.get_players(tags = [value.split("_")[1] for value in res.values])
                        for player in players:
                            if isinstance(player, coc.errors.NotFound):
                                continue
                            await _roster.move_member(player=player, new_roster=_new_roster)
                        embed = disnake.Embed(
                            description=f"{', '.join([player.name for player in players if not isinstance(player, coc.errors.NotFound)])} moved from **{_roster.roster_result.get('alias')}** to **{_new_roster.roster_result.get('alias')}** roster",
                            color=disnake.Color.green())
                        embed.set_thumbnail(url=_new_roster.roster_result.get("clan_badge"))
                        #await res.followup.send(embed=embed, ephemeral=True)
                        await _new_roster.find_roster(guild=ctx.guild, alias=_new_roster.roster_result.get("alias"))
                        await _roster.find_roster(guild=ctx.guild, alias=_roster.roster_result.get("alias"))
                        if mode == "move":
                            embed = await _roster.embed(move_text=f"Mode: {mode} | Moving to {new_roster}")
                        else:
                            embed = await _roster.embed(move_text=f"Mode: {mode}")
                        components = await _roster.mode_components(mode=mode, player_page=0)
                        await res.edit_original_message(embed=embed, components=components)
                    elif "roster_" in res.values[0]:
                        alias = res.values[0].split("_")[1]
                        await _roster.find_roster(guild=ctx.guild, alias=alias)
                        if mode == "move":
                            embed = await _roster.embed(move_text=f"Mode: {mode} | Moving to {new_roster}")
                        else:
                            embed = await _roster.embed(move_text=f"Mode: {mode}")
                        components = await _roster.mode_components(mode=mode, player_page=0)
                        await res.edit_original_message(embed=embed, components=components)
                    elif "rostermove_" in res.values[0]:
                        alias = res.values[0].split("_")[1]
                        new_roster = alias
                        await _new_roster.find_roster(guild=ctx.guild, alias=new_roster)
                        embed = await _roster.embed(move_text=f"Mode: {mode} | Moving to {new_roster}")
                        await res.edit_original_message(embed=embed)
            except Exception as error:
                if isinstance(error, RosterAliasAlreadyExists):
                    embed = disnake.Embed(description=f"Roster with this alias already exists.",
                                          color=disnake.Color.red())
                    await res.send(embed=embed, ephemeral=True)

                if isinstance(error, RosterDoesNotExist):
                    embed = disnake.Embed(description=f"Roster with this alias does not exist. Use `/roster create`",
                                          color=disnake.Color.red())
                    await res.send(embed=embed, ephemeral=True)

                if isinstance(error, PlayerAlreadyInRoster):
                    embed = disnake.Embed(description=f"Player has already been added to this roster.",
                                          color=disnake.Color.red())
                    await res.send(embed=embed, ephemeral=True)

                if isinstance(error, PlayerNotInRoster):
                    embed = disnake.Embed(description=f"Player not found in this roster.",
                                          color=disnake.Color.red())
                    await res.send(embed=embed, ephemeral=True)




        _new_roster = Roster(bot=self.bot)
        await _new_roster.find_roster(guild=ctx.guild, alias=new_roster)
        await _roster.move_member(player=player, new_roster=_new_roster)
        embed = disnake.Embed(
            description=f"{player.name} moved from **{_roster.roster_result.get('alias')}** to **{_new_roster.roster_result.get('alias')}** roster",
            color=disnake.Color.green())
        embed.set_thumbnail(url=_new_roster.roster_result.get("clan_badge"))


    @roster.sub_command(name="post", description="Post a roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_post(self, ctx: disnake.ApplicationCommandInteraction, roster: str):
        _roster = Roster(bot=self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        embed = await _roster.embed()
        await ctx.send(embed=embed)


    @roster.sub_command(name="refresh", description="Refresh the data in a roster (townhall levels, hero levels)")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_refresh(self, ctx: disnake.ApplicationCommandInteraction, roster: str):
        _roster = Roster(bot=self.bot)
        await ctx.response.defer()
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        await _roster.refresh_roster()
        embed = disnake.Embed(
            description=f"Player data for **{_roster.roster_result.get('alias')}** roster has been refreshed.",
            color=disnake.Color.green())
        embed.set_thumbnail(url=_roster.roster_result.get("clan_badge"))
        await ctx.edit_original_message(embed=embed)


    @roster.sub_command(name="missing", description="Players that aren't in the clan tied to the roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_missing(self, ctx: disnake.ApplicationCommandInteraction, roster: str, message:str =""):
        _roster = Roster(bot=self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        embed = await _roster.missing_embed()
        ping_buttons = [
            disnake.ui.Button(label="Ping Missing", emoji=self.bot.emoji.pin.partial_emoji, style=disnake.ButtonStyle.green,
                              custom_id=f"ping")
        ]
        buttons = disnake.ui.ActionRow()
        for button in ping_buttons:
            buttons.append_item(button)
        await ctx.send(embed=embed, components=[buttons])
        msg = await ctx.original_message()         
        if message != "":
            await _roster.set_missing_text(text=message)
        def check(res: disnake.MessageInteraction):
            return (res.message.id == msg.id) and (res.author.guild_permissions.manage_guild) and (res.user == ctx.user)

        try:
            res: disnake.MessageInteraction = await self.bot.wait_for("message_interaction", check=check, timeout=600)
        except:
            return await msg.edit(components=[])

        await res.response.defer()
        missing = await _roster.missing_list()
        tags = [member.get("tag") for member in missing]
        names = {}
        for member in missing:
            names[member.get("tag")] = member.get("name")
        links = await self.bot.link_client.get_links(*tags)
        missing_text = ""
        for player_tag, discord_id in links:
            member = disnake.utils.get(ctx.guild.members, id=discord_id)
            name = names[player_tag]
            if member is None:
                missing_text += f"{name} | {player_tag}\n"
            else:
                missing_text += f"{name} | {member.mention}\n"
        await msg.edit(components=[])
        await res.send(content=f"{_roster.missing_text}{missing_text}")


    @roster.sub_command(name="restrict", description="Restrict townhalls that can sign up")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_restrict(self, ctx: disnake.ApplicationCommandInteraction, roster: str, min:int = 1, max = "max"):
        _roster = Roster(bot=self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        await _roster.restrict_th(min=min, max=max)
        embed = disnake.Embed(
            description=f"**{_roster.roster_result.get('alias')}** signups have been restricted from Th{min} to Th{max}.",
            color=disnake.Color.green())
        embed.set_thumbnail(url=_roster.roster_result.get("clan_badge"))
        await ctx.send(embed=embed)


    @roster.sub_command(name="rename", description="Rename a roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_rename(self, ctx: disnake.ApplicationCommandInteraction, roster: str, new_name: str):
        _roster = Roster(bot=self.bot)
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        await _roster.rename(new_name=new_name)
        embed = disnake.Embed(
            description=f"Roster **{_roster.roster_result.get('alias')}** has been renamed to **{new_name}**",
            color=disnake.Color.green())
        embed.set_thumbnail(url=_roster.roster_result.get("clan_badge"))
        await ctx.send(embed=embed)


    @roster.sub_command(name="change-link", description="Change linked clan for roster")
    @commands.check_any(commands.has_permissions(manage_guild=True), check_commands())
    async def roster_change_link(self, ctx: disnake.ApplicationCommandInteraction, roster: str, clan: coc.Clan = commands.Param(converter=clan_converter)):
        _roster = Roster(bot=self.bot)
        await ctx.response.defer()
        await _roster.find_roster(guild=ctx.guild, alias=roster)
        await _roster.change_linked_clan(new_clan=clan)
        embed = disnake.Embed(
            description=f"Roster **{_roster.roster_result.get('alias')}** linked clan has been changed to **{clan.name}**",
            color=disnake.Color.green())
        embed.set_thumbnail(url=clan.badge.url)
        await ctx.edit_original_message(embed=embed)

    @roster_create.autocomplete("clan")
    @roster_change_link.autocomplete("clan")
    async def autocomp_clan(self, ctx: disnake.ApplicationCommandInteraction, query: str):
        tracked = self.bot.clan_db.find({"server": ctx.guild.id})
        limit = await self.bot.clan_db.count_documents(filter={"server": ctx.guild.id})
        clan_list = []
        for tClan in await tracked.to_list(length=limit):
            name = tClan.get("name")
            tag = tClan.get("tag")
            if query.lower() in name.lower():
                clan_list.append(f"{name} | {tag}")
        return clan_list[:25]

    @roster_delete.autocomplete("roster")
    @roster_create_signups.autocomplete("roster")
    @roster_post.autocomplete("roster")
    @roster_refresh.autocomplete("roster")
    @roster_missing.autocomplete("roster")
    @roster_add.autocomplete("roster")
    @roster_remove.autocomplete("roster")
    @roster_move.autocomplete("roster")
    @roster_move.autocomplete("new_roster")
    @roster_restrict.autocomplete("roster")
    @roster_rename.autocomplete("roster")
    @roster_change_link.autocomplete("roster")
    @roster_clear.autocomplete("roster")
    async def autocomp_rosters(self, ctx: disnake.ApplicationCommandInteraction, query: str):
        aliases = await self.bot.rosters.distinct("alias", filter={"server_id": ctx.guild.id})
        alias_list = []
        for alias in aliases:
            if query.lower() in alias.lower():
                alias_list.append(f"{alias}")
        return alias_list[:25]

    @roster_add.autocomplete("player")
    async def clan_player_tags(self, ctx: disnake.ApplicationCommandInteraction, query: str):
        names = await self.bot.family_names(query=query, guild=ctx.guild)
        return names

    @commands.Cog.listener()
    async def on_button_click(self, ctx: disnake.MessageInteraction):
        if "Signup_" in str(ctx.data.custom_id):
            alias = str(ctx.data.custom_id).split("_")[1]
            roster = Roster(bot=self.bot)
            await roster.find_roster(guild=ctx.guild, alias=alias)

            await ctx.response.defer()
            main_message = await ctx.original_message()
            linked_accounts = await self.bot.get_tags(ping=str(ctx.user.id))
            if not linked_accounts:
                return await ctx.send(content="No accounts linked to you. Use `/link` to get started.", ephemeral=True)
            accounts = await self.bot.get_players(tags=linked_accounts)
            options = []
            player_dict = {}
            roster_tags = [member.get("tag") for member in roster.players]
            for account in accounts:
                account: coc.Player
                if account.town_hall > roster.th_max or account.town_hall < roster.th_min:
                    continue
                if account.tag in roster_tags:
                    continue
                player_dict[account.tag] = account
                options.append(disnake.SelectOption(label=account.name, emoji=self.bot.partial_emoji_gen(self.bot.fetch_emoji(name=account.town_hall)), value=f"{account.tag}"))

            if not options:
                return await ctx.send(content="No accounts to add", ephemeral=True)
            options = options[:25]
            select = disnake.ui.Select(
                options=options,
                placeholder="Select Account(s)",
                # the placeholder text to show when no options have been chosen
                min_values=1,  # the minimum number of options a user must select
                max_values=len(options),  # the maximum number of options a user can select
            )
            dropdown = [disnake.ui.ActionRow(select)]
            msg = await ctx.followup.send(content="Select Account(s) to Add", components=dropdown, ephemeral=True)
            def check(res: disnake.MessageInteraction):
                return res.message.id == msg.id

            try:
                res: disnake.MessageInteraction = await self.bot.wait_for("message_interaction", check=check,timeout=600)
            except:
                return await msg.edit(components=[])

            await res.response.defer()
            accounts_to_add = res.values
            added = []
            for account in accounts_to_add:
                added.append(player_dict[account].name)
                await roster.add_member(player_dict[account])

            await res.edit_original_message(content=f"Added {', '.join(added)}", components=[])
            embed = await roster.embed()
            await main_message.edit(embed=embed)

        elif "RemoveMe_" in str(ctx.data.custom_id):
            alias = str(ctx.data.custom_id).split("_")[1]
            roster = Roster(bot=self.bot)
            await roster.find_roster(guild=ctx.guild, alias=alias)

            await ctx.response.defer()
            main_message = await ctx.original_message()
            linked_accounts = await self.bot.get_tags(ping=str(ctx.user.id))
            if not linked_accounts:
                return await ctx.send(content="No accounts linked to you. Use `/link` to get started.", ephemeral=True)
            accounts = await self.bot.get_players(tags=linked_accounts)
            options = []
            player_dict = {}
            roster_tags = [member.get("tag") for member in roster.players]
            for account in accounts:
                account: coc.Player
                if account.town_hall > roster.th_max or account.town_hall < roster.th_min:
                    continue
                if account.tag not in roster_tags:
                    continue
                player_dict[account.tag] = account
                options.append(disnake.SelectOption(label=account.name, emoji=self.bot.partial_emoji_gen(
                    self.bot.fetch_emoji(name=account.town_hall)), value=f"{account.tag}"))

            if not options:
                return await ctx.send(content="No accounts to remove", ephemeral=True)
            options = options[:25]
            select = disnake.ui.Select(
                options=options,
                placeholder="Select Account(s)",
                # the placeholder text to show when no options have been chosen
                min_values=1,  # the minimum number of options a user must select
                max_values=len(options),  # the maximum number of options a user can select
            )
            dropdown = [disnake.ui.ActionRow(select)]
            msg = await ctx.followup.send(content="Select Account(s) to Remove", components=dropdown, ephemeral=True)

            def check(res: disnake.MessageInteraction):
                return res.message.id == msg.id

            try:
                res: disnake.MessageInteraction = await self.bot.wait_for("message_interaction", check=check,
                                                                          timeout=600)
            except:
                return await msg.edit(components=[])

            await res.response.defer()
            accounts_to_add = res.values
            added = []

            for account in accounts_to_add:
                added.append(player_dict[account].name)
                await roster.remove_member(player_dict[account])

            await res.edit_original_message(content=f"Removed {', '.join(added)}", components=[])
            embed = await roster.embed()
            await main_message.edit(embed=embed)

'''
    @commands.group(name="roster", pass_context=True, invoke_without_command=True)
    async def roster_co(self, ctx, *, alias=None):
        if alias is None:
            await ctx.send(f"Alias is a required argument. `{ctx.prefix}roster [alias]")
        roster = self.bot.get_cog("Roster")
        valid_alias = await roster.is_valid_alias(alias, ctx.guild.id)
        if not valid_alias:
            embed = disnake.Embed(description=f"A roster with that alias/name does not exist.\nUse `{ctx.prefix}roster list` to see server rosters & aliases.",
                                  color=disnake.Color.red())
            return await ctx.send(embed=embed)

        embeds = await roster.create_roster_embeds(alias, ctx.guild.id)
        for embed in embeds:
            await ctx.send(embed=embed)


    @roster_co.group(name="create", pass_context=True, invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_roles=True), check_commands())
    async def roster_create(self, ctx):

        roster = self.bot.get_cog("Roster")
        member_list = await roster.get_members(ctx)
        if member_list is None:
            return
        alias = await roster.get_alias(ctx)
        if alias is None:
            return

        await rosters.insert_one({
            "server": ctx.guild.id,
            "members": member_list[0],
            "clan" : member_list[1],
            "alias": alias
        })

        embed = disnake.Embed(title=f"Roster ({alias}) successfully added.",
                              description=f"Alias: {alias}\n"
                                          f"Linked Clan: {member_list[1]}",
                              color=disnake.Color.green())
        embed.set_thumbnail(url=ctx.guild.icon_url_as())
        await roster.msg.edit(embed=embed)


    @roster_co.group(name="edit", pass_context=True, invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_roles=True), check_commands())
    async def roster_edit(self, ctx, *, alias=None):
        if alias is None:
            await ctx.send(f"Alias is a required argument. `{ctx.prefix}roster edit [alias]")
        added = ""
        removed = ""
        mode = "Add"
        roster = self.bot.get_cog("Roster")
        valid_alias = await roster.is_valid_alias(alias, ctx.guild.id)
        if not valid_alias:
            embed = disnake.Embed(
                description=f"A roster with that alias/name does not exist.\nUse `{ctx.prefix}roster list` to see server rosters & aliases.",
                color=disnake.Color.red())
            return await ctx.send(embed=embed)

        text = await roster.create_member_list(alias, ctx.guild.id)
        clan = await roster.linked_clan(alias, ctx.guild.id)

        embed = disnake.Embed(title=f"{clan.name} Roster",
            description=text,
            color=disnake.Color.green())

        stat_buttons = [
            create_button(label="Add", emoji="➕", custom_id="Add", style=ButtonStyle.green),
            create_button(label="Remove", emoji="➖", custom_id="Remove", style=ButtonStyle.red),
            create_button(label="Save", emoji="💾", custom_id="Save", style=ButtonStyle.grey)]
        buttons = create_actionrow(*stat_buttons)
        embed.set_footer(text=f"Currently in {mode} mode.")
        msg = await ctx.send(content="Use the buttons to switch between add or remove modes.\n"
                                     "**ADD** - Send PlayerTag or Mention player in chat to add to roster\n"
                                     "**REMOVE** - Send number on roster (i.e 15)\n"
                                     "**SAVE** - Save roster & get log of changes.\n"
                                     "**NOTE:** If its an invalid option for add or remove, the list will stay unchanged.",embed=embed, components=[buttons])



        while True:
            def check(res):
                return res.author_id == ctx.message.author.id

            def check2(message):
                ctx.message.content = message.content
                return message.content != "" and message.author == ctx.message.author and message.channel == ctx.message.channel

            try:
                button = wait_for_component(self.bot, components=[buttons],messages=msg, timeout=600, check=check)
                text_res = self.bot.wait_for('message', check=check2, timeout=300)
            except:
                return await msg.edit(components=[])


            button = asyncio.create_task(button)
            text_res = asyncio.create_task(text_res)

            tasks = [button, text_res]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            if text_res in done:
                text_res = await text_res
                await text_res.delete()
                if mode == "Add":
                    try:
                        tag = text_res.content
                        player = await getPlayer(tag)
                        tag = player.tag
                        await roster.add_member(alias, ctx.guild.id, tag)
                        added += f"[{player.name}]({player.share_link}) | {player.tag}\n"
                        text = await roster.create_member_list(alias, ctx.guild.id)
                        embed = disnake.Embed(title=f"{clan.name} Roster",
                                              description=text,
                                              color=disnake.Color.green())

                        embed.set_footer(text=f"Currently in {mode} mode.")
                        await msg.edit(embed=embed, components=[buttons])
                        continue
                    except:
                        pass

                    try:
                        ping = text_res.content
                        tags = await getTags(ctx, ping)
                        if tags == []:
                            continue
                        options = []
                        async for player in coc_client.get_players(tags):
                            emoji = emojiDictionary(player.town_hall)
                            emoji = emoji.split(":", 2)
                            emoji = emoji[2]
                            emoji = emoji[0:len(emoji) - 1]
                            emoji = self.bot.get_emoji(int(emoji))
                            emoji = disnake.PartialEmoji(name=emoji.name, id=emoji.id)
                            options.append(create_select_option(f"{player.name}", value=f"{player.tag}", emoji=emoji))

                        select1 = create_select(
                            options=options,
                            placeholder="Choose player to add to roster.",
                            min_values=1,  # the minimum number of options a user must select
                            max_values=1  # the maximum number of options a user can select
                        )
                        action_row = create_actionrow(select1)

                        msg2 = await ctx.reply(content="Choose player to add to roster.", components=[action_row],
                                              mention_author=False)

                        value = None
                        while value is None:
                            try:
                                res = await wait_for_component(self.bot, components=action_row,
                                                               messages=msg2, timeout=600)
                            except:
                                await msg.edit(components=[])
                                break

                            if res.author_id != ctx.author.id:
                                await res.send(content="You must run the command to interact with components.",
                                               hidden=True)
                                continue

                            await res.edit_origin()
                            value = res.values[0]

                        await msg2.delete()
                        await roster.add_member(alias, ctx.guild.id, value)
                        player = await getPlayer(value)
                        added += f"[{player.name}]({player.share_link}) | {player.tag}\n"
                        text = await roster.create_member_list(alias, ctx.guild.id)
                        embed = disnake.Embed(title=f"{clan.name} Roster",
                                              description=text,
                                              color=disnake.Color.green())

                        embed.set_footer(text=f"Currently in {mode} mode.")
                        await msg.edit(embed=embed, components=[buttons])
                        continue
                    except:
                        pass


                elif mode == "Remove":
                    try:
                        num = int(text_res.content)
                        member_list = await roster.fetch_members(alias, ctx.guild.id)
                        tag = member_list[num-1]
                        await roster.remove_member(alias,ctx.guild.id, tag)
                        player = await getPlayer(tag)
                        removed+= f"[{player.name}]({player.share_link}) | {player.tag}\n"
                        text = await roster.create_member_list(alias, ctx.guild.id)
                        embed = disnake.Embed(title=f"{clan.name} Roster",
                                              description=text,
                                              color=disnake.Color.green())

                        embed.set_footer(text=f"Currently in {mode} mode.")
                        await msg.edit(embed=embed, components=[buttons])
                        continue
                    except:
                        pass

            elif button in done:
                button = await button
                #print("here2")
                await button.edit_origin()
                mode = button.custom_id
                text = await roster.create_member_list(alias, ctx.guild.id)
                embed = disnake.Embed(title=f"{clan.name} Roster",
                                      description=text,
                                      color=disnake.Color.green())

                embed.set_footer(text=f"Currently in {mode} mode.")
                await msg.edit(embed=embed, components=[buttons])
                if mode == "Save":
                    embed.set_footer(text="Roster Saved")
                    if added == "":
                        added = "None"
                    if removed == "":
                        removed = "None"
                    embed2 = disnake.Embed(title="Changes Made:",
                        description=f"Players added:\n{added}\nPlayers Removed:\n{removed}",
                        color=disnake.Color.green())
                    await ctx.reply(embed=embed2, mention_author=False)
                    return await msg.edit(embed =embed,components=[])


    @roster_co.group(name="list", pass_context=True, invoke_without_command=True)
    async def roster_list(self, ctx):
        roster = self.bot.get_cog("Roster")
        text = await roster.create_alias_list(ctx.guild.id)
        embed = disnake.Embed(title=f"**{ctx.guild} CWL Rosters List:**",
                              description=text,
                              color=disnake.Color.green())
        embed.set_thumbnail(url=ctx.guild.icon_url_as())
        await ctx.send(embed=embed)

    @roster_co.group(name="delete", pass_context=True, invoke_without_command=True)
    @commands.check_any(commands.has_permissions(manage_roles=True), check_commands())
    async def roster_remove(self, ctx, *, alias=None):
        if alias is None:
            return await ctx.send(f"Alias is a required argument. `{ctx.prefix}roster remove [alias]")
        roster = self.bot.get_cog("Roster")
        valid_alias = await roster.is_valid_alias(alias, ctx.guild.id)
        if not valid_alias:
            embed = disnake.Embed(
                description=f"A roster with that alias/name does not exist.\nUse `{ctx.prefix}roster list` to see server rosters & aliases.",
                color=disnake.Color.red())
            return await ctx.send(embed=embed)

        await rosters.find_one_and_delete({"$and": [
            {"alias": alias},
            {"server": ctx.guild.id}
        ]})

        embed = disnake.Embed(description=f"{alias} Roster Removed",
                              color=disnake.Color.green())
        embed.set_thumbnail(url=ctx.guild.icon_url_as())
        await ctx.send(embed=embed)

    @roster_co.group(name="compare", pass_context=True, invoke_without_command=True)
    async def roster_compare(self, ctx, clan=None, *, alias=None):
        if clan is None or alias is None:
            await ctx.send(f"Alias and Clan are required arguments. `{ctx.prefix}roster compare [clan] [alias]")

        clan = clan.lower()
        results = await clans.find_one({"$and": [
            {"alias": clan},
            {"server": ctx.guild.id}
        ]})

        if results is not None:
            tag = results.get("tag")
            clan = await getClan(tag)
        else:
            clan = await getClan(clan)

        if clan is None:
            return await ctx.reply("Not a valid clan tag.",
                                   mention_author=False)

        roster = self.bot.get_cog("Roster")
        valid_alias = await roster.is_valid_alias(alias, ctx.guild.id)
        if not valid_alias:
            embed = disnake.Embed(
                description=f"A roster with that alias/name does not exist.\nUse `{ctx.prefix}roster list` to see server rosters & aliases.",
                color=disnake.Color.red())
            return await ctx.send(embed=embed)

        members = await roster.fetch_members(alias, ctx.guild.id)

        clan_members = []
        for m in clan.members:
            clan_members.append(m.tag)

        not_present = ""
        for member in members:
            if member not in clan_members:
                member = await getPlayer(member)
                not_present += f"{member.name}\n"
        if not_present == "":
            not_present = "None"
        embed = disnake.Embed(title=f"{clan.name} Roster/Clan Comparison",
            description=f"Missing Members:\n{not_present}",
            color=disnake.Color.green())
        return await ctx.send(embed=embed)
    '''


def setup(bot: CustomClient):
    bot.add_cog(Roster_Commands(bot))
