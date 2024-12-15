import requests
from pydantic import BaseModel
from datetime import datetime

from module.cfg import guild_id


class ClanBattleBoss(BaseModel):
    id: str
    name: dict[str, str]
    avatar: str


class AttributeBuilds(BaseModel):
    fire: str
    water: str
    wind: str
    light: str
    dark: str


class MasterSkillBuilds(BaseModel):
    left: str
    center: str
    right: str
    core: str
    master: str


class RequiredBuild(BaseModel):
    attributes: AttributeBuilds
    masterSkills: MasterSkillBuilds


class ClanBattle(BaseModel):
    id: str
    year: int
    month: int
    startAt: datetime
    endAt: datetime
    bosses: list[ClanBattleBoss]
    maxRank: str
    maxLevel: int
    maxUniqueEquipment: int
    requiredBuild: RequiredBuild


class DiscordMessageReceiver(BaseModel):
    threadId: int | None
    imageMessageId1: int | None
    imageMessageId2: int | None
    timelineMessageId1: int | None
    timelineMessageId2: int | None
    timelineMessageId3: int | None


class CharacterTag(BaseModel):
    key: str
    value: str


class Character(BaseModel):
    id: str
    name: dict[str, str]
    avatar: str
    star: int
    uniqueEquipment: int
    position: float
    attribute: str
    aliases: list[str]
    tags: list[CharacterTag] | None


class TeamMember(BaseModel):
    character: Character
    star: int
    isMax: bool
    remark: str


class Guide(BaseModel):
    id: str
    clanBattleId: str
    name: str
    boss: ClanBattleBoss | None
    damage: str
    teamMembers: list[TeamMember]
    author: str
    remark: str
    timeline: str


class DiscordReleaseJob(BaseModel):
    id: str
    releaseId: str
    type: str
    version: int
    guildId: int
    channelId: int
    receivers: dict[str, DiscordMessageReceiver] | None
    state: str
    clanBattle: ClanBattle
    guides: list[Guide]
    createdAt: datetime
    updatedAt: datetime


api_host = "http://pcr-backend_devcontainer-app-1"


def get_clan_battle_id() -> str:
    return datetime.now().strftime("%Y%m")


async def fetch_job() -> DiscordReleaseJob | None:
    response = requests.post(
        f"{api_host}/clan-battles/{get_clan_battle_id()}/guide-release-jobs/fetch-next",
        json={"guildId": guild_id()},
    )
    data = response.json()
    if data is None:
        return None

    job = DiscordReleaseJob(**data)
    return job


async def close_job(jobId: str, receivers: dict[str, DiscordMessageReceiver]) -> None:
    receivers_json = {}
    for boss_id, receiver in receivers.items():
        receivers_json[boss_id] = receiver.model_dump()

    response = requests.post(
        f"{api_host}/clan-battles/{get_clan_battle_id()}/guide-release-jobs/{jobId}/close",
        json={"receivers": receivers_json},
    )


async def get_team_sheet(
    job: DiscordReleaseJob, boss: ClanBattleBoss, start_index: int
) -> bytes | None:
    teams: list[Team2] = []
    for guide in [
        guide
        for guide in job.guides
        if guide.boss is not None and guide.boss.id == boss.id
    ]:
        teams.append(
            Team2(
                id=guide.name,
                boss=boss,
                damage=guide.damage,
                members=[
                    TeamMember2(
                        name=member.character.name["zh-Hant"],
                        avatar=member.character.avatar,
                        star=member.star,
                        attribute=member.character.attribute,
                        remark=member.remark,
                    )
                    for member in guide.teamMembers
                ],
                author=guide.author,
                attributes=job.clanBattle.requiredBuild.attributes,
                routes=job.clanBattle.requiredBuild.masterSkills,
                remark=guide.remark,
            )
        )

    teams = teams[start_index:]
    if len(teams) == 0:
        return None

    req = GenerateTeamSheetRequest(
        boss=boss,
        teams=teams,
        routes=job.clanBattle.requiredBuild.masterSkills,
        attributes=job.clanBattle.requiredBuild.attributes,
        startSequence=start_index + 1,
    )

    response = requests.post(
        f"{api_host}/clanbattles/team-sheet",
        json=req.model_dump(),
    )

    # 檢查回應狀態碼
    if response.status_code != 200:
        raise Exception("無法生成團表圖片")

    return response.content


class TeamMember2(BaseModel):
    name: str
    avatar: str
    star: int
    attribute: str
    remark: str


class Team2(BaseModel):
    id: str
    boss: ClanBattleBoss
    damage: str
    members: list[TeamMember2]
    author: str
    attributes: AttributeBuilds
    routes: MasterSkillBuilds
    remark: str


class GenerateTeamSheetRequest(BaseModel):
    boss: ClanBattleBoss
    teams: list[Team2]
    routes: MasterSkillBuilds
    attributes: AttributeBuilds
    startSequence: int | None
