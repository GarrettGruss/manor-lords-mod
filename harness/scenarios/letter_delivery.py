"""An AI lord sends a letter to the player through the helper mod. Check the InBox of the player."""

NAME = "letter-delivery"
DESCRIPTION = "Send the welcome letter of Hildebolt with the action send_letter. The InBox must hold one more letter, from an AI lord."
LIMIT_S = 60
PARAGRAPH = "welcome_from_hildebolt"


def run(ctx) -> dict:
    expect = ctx.expect
    record = ctx.actions.send_letter([PARAGRAPH])
    expect.equals("letters in the InBox", record["after"]["count"] - record["before"]["count"], 1)

    inbox = ctx.bridge.read_property(ctx.bridge.player_path(), "InBox")
    letter = inbox[-1]
    expect.equals("letter paragraphs", letter["paras"], [PARAGRAPH])
    # The `read` flag is not checked: it was false in one real run and true in two others.
    expect.equals("sender is an AI lord", "PawnCPP_AI" in letter["sender"]["__object"], True)
    return ctx.result()
